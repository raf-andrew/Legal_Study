<?php

namespace App\Mcp\Service;

use App\Mcp\ConfigurationManager;
use App\Mcp\EventBus;
use Illuminate\Support\Facades\Log;
use Illuminate\Support\Collection;
use Illuminate\Support\Facades\Config;
use Illuminate\Support\Facades\File;
use ReflectionClass;

class Discovery
{
    protected $services = [];
    protected $config;
    protected $eventBus;

    public function __construct(ConfigurationManager $config, EventBus $eventBus)
    {
        $this->config = $config;
        $this->eventBus = $eventBus;
        $this->initialize();
    }

    protected function initialize()
    {
        if (!$this->config->get('services.discovery.enabled', true)) {
            return;
        }

        $this->discoverServices();
        $this->startDiscoveryLoop();
    }

    protected function discoverServices()
    {
        $paths = $this->config->get('services.discovery.paths', [
            app_path('Services'),
            app_path('Http/Controllers'),
            app_path('Console/Commands'),
        ]);

        foreach ($paths as $path) {
            if (!File::exists($path)) {
                continue;
            }

            $files = File::allFiles($path);
            foreach ($files as $file) {
                $this->processFile($file);
            }
        }

        Log::info("MCP Service Discovery: Found " . count($this->services) . " services");
    }

    protected function processFile($file)
    {
        $class = $this->getClassFromFile($file);
        if (!$class) {
            return;
        }

        try {
            $reflection = new ReflectionClass($class);
            if ($reflection->isAbstract() || $reflection->isInterface()) {
                return;
            }

            $this->registerService($class, $reflection);
        } catch (\ReflectionException $e) {
            Log::warning("MCP Service Discovery: Failed to process {$class}: " . $e->getMessage());
        }
    }

    protected function getClassFromFile($file)
    {
        $content = File::get($file);
        $namespace = '';
        $class = '';

        if (preg_match('/namespace\s+(.+?);/s', $content, $matches)) {
            $namespace = $matches[1];
        }

        if (preg_match('/class\s+(\w+)/', $content, $matches)) {
            $class = $matches[1];
        }

        return $namespace ? "{$namespace}\\{$class}" : $class;
    }

    protected function registerService($class, ReflectionClass $reflection)
    {
        $service = [
            'name' => $class,
            'type' => $this->determineServiceType($reflection),
            'methods' => $this->getServiceMethods($reflection),
            'metadata' => $this->getServiceMetadata($reflection),
        ];

        $this->services[$class] = $service;
        $this->eventBus->publish('service.discovered', $service);
    }

    protected function determineServiceType(ReflectionClass $reflection)
    {
        if ($reflection->implementsInterface('Illuminate\\Contracts\\Http\\Kernel')) {
            return 'http_kernel';
        }

        if ($reflection->implementsInterface('Illuminate\\Contracts\\Console\\Kernel')) {
            return 'console_kernel';
        }

        if ($reflection->implementsInterface('Illuminate\\Contracts\\Queue\\Queue')) {
            return 'queue';
        }

        if ($reflection->implementsInterface('Illuminate\\Contracts\\Cache\\Repository')) {
            return 'cache';
        }

        return 'service';
    }

    protected function getServiceMethods(ReflectionClass $reflection)
    {
        $methods = [];
        foreach ($reflection->getMethods() as $method) {
            if ($method->isPublic() && !$method->isConstructor()) {
                $methods[] = $method->getName();
            }
        }
        return $methods;
    }

    protected function getServiceMetadata(ReflectionClass $reflection)
    {
        return [
            'is_abstract' => $reflection->isAbstract(),
            'is_final' => $reflection->isFinal(),
            'is_interface' => $reflection->isInterface(),
            'is_trait' => $reflection->isTrait(),
            'interfaces' => array_map(function ($interface) {
                return $interface->getName();
            }, $reflection->getInterfaces()),
            'traits' => array_map(function ($trait) {
                return $trait->getName();
            }, $reflection->getTraits()),
        ];
    }

    protected function startDiscoveryLoop()
    {
        $interval = $this->config->get('services.discovery.interval', 60);
        if ($interval > 0) {
            $this->eventBus->subscribe('discovery.tick', function () {
                $this->discoverServices();
            });
        }
    }

    public function getService($name)
    {
        return $this->services[$name] ?? null;
    }

    public function getServices()
    {
        return new Collection($this->services);
    }

    public function getServicesByType($type)
    {
        return $this->getServices()->filter(function ($service) use ($type) {
            return $service['type'] === $type;
        });
    }
} 