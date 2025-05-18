<?php

namespace App\Services;

use Illuminate\Support\Collection;
use Illuminate\Support\Facades\File;
use ReflectionClass;
use ReflectionMethod;

class Discovery
{
    private Collection $discoveredServices;
    private array $serviceTypes = [];
    private string $servicesPath;

    public function __construct(string $servicesPath = null)
    {
        $this->discoveredServices = new Collection();
        $this->servicesPath = $servicesPath ?? app_path('Services');
    }

    public function discoverServices(): Collection
    {
        $files = File::allFiles($this->servicesPath);
        
        foreach ($files as $file) {
            if ($file->getExtension() !== 'php') {
                continue;
            }

            $className = $this->getFullyQualifiedClassName($file->getPathname());
            if (!$className || !class_exists($className)) {
                continue;
            }

            $reflection = new ReflectionClass($className);
            if ($reflection->isAbstract() || $reflection->isInterface()) {
                continue;
            }

            $serviceMetadata = $this->extractServiceMetadata($reflection);
            if ($serviceMetadata) {
                $this->discoveredServices->put($className, $serviceMetadata);
            }
        }

        return $this->discoveredServices;
    }

    private function getFullyQualifiedClassName(string $filepath): ?string
    {
        $contents = file_get_contents($filepath);
        if (preg_match('/namespace\s+(.+?);/s', $contents, $matches)) {
            $namespace = $matches[1];
            $className = pathinfo($filepath, PATHINFO_FILENAME);
            return $namespace . '\\' . $className;
        }
        return null;
    }

    private function extractServiceMetadata(ReflectionClass $reflection): ?array
    {
        $methods = $reflection->getMethods(ReflectionMethod::IS_PUBLIC);
        $serviceMetadata = [
            'name' => $reflection->getShortName(),
            'type' => $this->determineServiceType($reflection),
            'methods' => [],
            'dependencies' => $this->extractDependencies($reflection),
            'attributes' => $this->extractAttributes($reflection)
        ];

        foreach ($methods as $method) {
            $serviceMetadata['methods'][] = [
                'name' => $method->getName(),
                'parameters' => $this->extractMethodParameters($method),
                'returnType' => $method->getReturnType() ? (string)$method->getReturnType() : 'mixed',
                'attributes' => $this->extractAttributes($method)
            ];
        }

        return $serviceMetadata;
    }

    private function determineServiceType(ReflectionClass $reflection): string
    {
        foreach ($this->serviceTypes as $type => $interface) {
            if ($reflection->implementsInterface($interface)) {
                return $type;
            }
        }
        return 'generic';
    }

    private function extractDependencies(ReflectionClass $reflection): array
    {
        $constructor = $reflection->getConstructor();
        if (!$constructor) {
            return [];
        }

        $dependencies = [];
        foreach ($constructor->getParameters() as $parameter) {
            $dependencies[] = [
                'name' => $parameter->getName(),
                'type' => $parameter->getType() ? (string)$parameter->getType() : 'mixed',
                'required' => !$parameter->isOptional()
            ];
        }
        return $dependencies;
    }

    private function extractMethodParameters(ReflectionMethod $method): array
    {
        $parameters = [];
        foreach ($method->getParameters() as $parameter) {
            $parameters[] = [
                'name' => $parameter->getName(),
                'type' => $parameter->getType() ? (string)$parameter->getType() : 'mixed',
                'required' => !$parameter->isOptional(),
                'default' => $parameter->isOptional() ? $this->getParameterDefaultValue($parameter) : null
            ];
        }
        return $parameters;
    }

    private function extractAttributes($reflection): array
    {
        $attributes = [];
        foreach ($reflection->getAttributes() as $attribute) {
            $attributes[] = [
                'name' => $attribute->getName(),
                'arguments' => $attribute->getArguments()
            ];
        }
        return $attributes;
    }

    private function getParameterDefaultValue($parameter)
    {
        return $parameter->isDefaultValueAvailable() ? $parameter->getDefaultValue() : null;
    }

    public function registerServiceType(string $type, string $interface): void
    {
        $this->serviceTypes[$type] = $interface;
    }
} 