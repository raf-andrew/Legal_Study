<?php

namespace LegalStudy\Initialization;

use LegalStudy\Initialization\InitializationInterface;
use LegalStudy\Initialization\InitializationStatus;

class InitializationStateManager
{
    private array $states = [];
    private array $dependencies = [];
    private array $initializationOrder = [];

    public function registerInitialization(InitializationInterface $initialization, array $dependencies = []): void
    {
        $name = get_class($initialization);
        $this->states[$name] = [
            'status' => new InitializationStatus(),
            'startTime' => null,
            'endTime' => null,
            'errors' => [],
            'warnings' => [],
            'instance' => $initialization
        ];

        // Initialize dependencies array with only non-empty dependencies
        $this->dependencies[$name] = array_values(array_filter($dependencies));
    }

    public function updateState(string $name, InitializationStatus $status): void
    {
        if (!isset($this->states[$name])) {
            throw new \RuntimeException("Initialization {$name} not registered");
        }

        $this->states[$name]['status'] = $status;
        $this->states[$name]['endTime'] = microtime(true);
    }

    public function getState(string $name): array
    {
        if (!isset($this->states[$name])) {
            throw new \RuntimeException("Initialization {$name} not registered");
        }

        return $this->states[$name];
    }

    public function getAllStates(): array
    {
        return $this->states;
    }

    public function isInitializationComplete(string $name): bool
    {
        if (!isset($this->states[$name])) {
            return false;
        }

        return $this->states[$name]['status']->isComplete();
    }

    public function isAllComplete(): bool
    {
        foreach ($this->states as $state) {
            if (!$state['status']->isComplete()) {
                return false;
            }
        }
        return true;
    }

    public function getInitializationOrder(): array
    {
        $visited = [];
        $order = [];
        $path = [];

        foreach (array_keys($this->states) as $className) {
            if (!isset($visited[$className])) {
                $this->visit($className, $visited, $order, $path);
            }
        }

        return $order;
    }

    private function visit(string $className, array &$visited, array &$order, array &$path): void
    {
        if (!isset($this->dependencies[$className])) {
            throw new \RuntimeException("Class $className is not registered");
        }

        if (in_array($className, $path)) {
            $cycle = array_slice($path, array_search($className, $path));
            $cycle[] = $className;
            throw new \RuntimeException("Circular dependency detected: " . implode(" -> ", $cycle));
        }

        if (isset($visited[$className])) {
            return; // Already visited
        }

        $path[] = $className;
        $visited[$className] = true;

        foreach ($this->dependencies[$className] as $dependency) {
            $this->visit($dependency, $visited, $order, $path);
        }

        array_pop($path);
        if (!in_array($className, $order)) {
            $order[] = $className;
        }
    }

    public function getDependencies(string $name): array
    {
        if (!isset($this->states[$name])) {
            throw new \RuntimeException("Initialization {$name} not registered");
        }
        return $this->dependencies[$name] ?? [];
    }

    public function hasDependencies(string $className): bool
    {
        if (!isset($this->dependencies[$className])) {
            throw new \RuntimeException("Class $className is not registered");
        }
        return !empty($this->dependencies[$className]);
    }

    public function getInitialization(string $name): ?InitializationInterface
    {
        return $this->states[$name]['instance'] ?? null;
    }

    public function getInitializationStatus(string $name): ?InitializationStatus
    {
        return $this->states[$name]['status'] ?? null;
    }

    public function getInitializationErrors(string $name): array
    {
        return $this->states[$name]['errors'] ?? [];
    }

    public function getInitializationWarnings(string $name): array
    {
        return $this->states[$name]['warnings'] ?? [];
    }
} 