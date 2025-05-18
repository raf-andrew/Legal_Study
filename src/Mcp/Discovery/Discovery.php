<?php

namespace Mcp\Discovery;

use Illuminate\Support\Collection;
use ReflectionClass;
use ReflectionMethod;

class Discovery
{
    /**
     * @var Collection
     */
    protected $services;

    /**
     * @var array
     */
    protected $serviceTypes = [];

    /**
     * @var array
     */
    protected $excludedPaths = [
        'vendor',
        'storage',
        'bootstrap',
        'tests',
    ];

    /**
     * Discovery constructor.
     */
    public function __construct()
    {
        $this->services = new Collection();
    }

    /**
     * Scan the application for services
     *
     * @param string $basePath
     * @return Collection
     */
    public function scanServices(string $basePath): Collection
    {
        $this->services = new Collection();
        
        $this->scanDirectory($basePath);
        
        return $this->services;
    }

    /**
     * Scan a directory for services
     *
     * @param string $path
     */
    protected function scanDirectory(string $path): void
    {
        $files = scandir($path);
        
        foreach ($files as $file) {
            if ($file === '.' || $file === '..') {
                continue;
            }
            
            $fullPath = $path . DIRECTORY_SEPARATOR . $file;
            
            if (is_dir($fullPath)) {
                if (!$this->isExcludedPath($fullPath)) {
                    $this->scanDirectory($fullPath);
                }
                continue;
            }
            
            if (pathinfo($file, PATHINFO_EXTENSION) === 'php') {
                $this->processFile($fullPath);
            }
        }
    }

    /**
     * Check if a path should be excluded from scanning
     *
     * @param string $path
     * @return bool
     */
    protected function isExcludedPath(string $path): bool
    {
        foreach ($this->excludedPaths as $excludedPath) {
            if (strpos($path, $excludedPath) !== false) {
                return true;
            }
        }
        
        return false;
    }

    /**
     * Process a PHP file for service discovery
     *
     * @param string $filePath
     */
    protected function processFile(string $filePath): void
    {
        $className = $this->getClassNameFromFile($filePath);
        
        if (!$className) {
            return;
        }
        
        try {
            $reflection = new ReflectionClass($className);
            
            if ($this->isServiceClass($reflection)) {
                $this->registerService($reflection);
            }
        } catch (\ReflectionException $e) {
            // Log error or handle as needed
        }
    }

    /**
     * Get the class name from a PHP file
     *
     * @param string $filePath
     * @return string|null
     */
    protected function getClassNameFromFile(string $filePath): ?string
    {
        $content = file_get_contents($filePath);
        
        if (preg_match('/namespace\s+([^;]+);/', $content, $matches)) {
            $namespace = $matches[1];
            
            if (preg_match('/class\s+([^\s]+)/', $content, $matches)) {
                return $namespace . '\\' . $matches[1];
            }
        }
        
        return null;
    }

    /**
     * Check if a class is a service class
     *
     * @param ReflectionClass $reflection
     * @return bool
     */
    protected function isServiceClass(ReflectionClass $reflection): bool
    {
        // Add your service detection logic here
        // For example, check for specific interfaces or traits
        return true;
    }

    /**
     * Register a service
     *
     * @param ReflectionClass $reflection
     */
    protected function registerService(ReflectionClass $reflection): void
    {
        $service = [
            'class' => $reflection->getName(),
            'methods' => $this->getServiceMethods($reflection),
            'metadata' => $this->getServiceMetadata($reflection),
        ];
        
        $this->services->push($service);
    }

    /**
     * Get service methods
     *
     * @param ReflectionClass $reflection
     * @return array
     */
    protected function getServiceMethods(ReflectionClass $reflection): array
    {
        $methods = [];
        
        foreach ($reflection->getMethods(ReflectionMethod::IS_PUBLIC) as $method) {
            if ($method->isConstructor() || $method->isDestructor()) {
                continue;
            }
            
            $methods[] = [
                'name' => $method->getName(),
                'parameters' => $this->getMethodParameters($method),
                'returnType' => $method->getReturnType() ? $method->getReturnType()->getName() : null,
            ];
        }
        
        return $methods;
    }

    /**
     * Get method parameters
     *
     * @param ReflectionMethod $method
     * @return array
     */
    protected function getMethodParameters(ReflectionMethod $method): array
    {
        $parameters = [];
        
        foreach ($method->getParameters() as $parameter) {
            $parameters[] = [
                'name' => $parameter->getName(),
                'type' => $parameter->getType() ? $parameter->getType()->getName() : null,
                'default' => $parameter->isDefaultValueAvailable() ? $parameter->getDefaultValue() : null,
                'required' => !$parameter->isOptional(),
            ];
        }
        
        return $parameters;
    }

    /**
     * Get service metadata
     *
     * @param ReflectionClass $reflection
     * @return array
     */
    protected function getServiceMetadata(ReflectionClass $reflection): array
    {
        return [
            'namespace' => $reflection->getNamespaceName(),
            'shortName' => $reflection->getShortName(),
            'isAbstract' => $reflection->isAbstract(),
            'isFinal' => $reflection->isFinal(),
            'interfaces' => $reflection->getInterfaceNames(),
            'traits' => $reflection->getTraitNames(),
            'parentClass' => $reflection->getParentClass() ? $reflection->getParentClass()->getName() : null,
        ];
    }

    /**
     * Get all discovered services
     *
     * @return Collection
     */
    public function getServices(): Collection
    {
        return $this->services;
    }

    /**
     * Get services by type
     *
     * @param string $type
     * @return Collection
     */
    public function getServicesByType(string $type): Collection
    {
        return $this->services->filter(function ($service) use ($type) {
            return isset($service['metadata']['interfaces']) && 
                   in_array($type, $service['metadata']['interfaces']);
        });
    }
} 