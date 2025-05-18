<?php

namespace LegalStudy\ModularInitialization\Services;

use LegalStudy\ModularInitialization\AbstractInitialization;
use LegalStudy\ModularInitialization\Exceptions\CircularDependencyException;

class InitializationStateManager
{
    private InitializationStatus $status;
    private array $initializations = [];
    private array $dependencies = [];
    private array $initializationOrder = [];

    public function __construct(InitializationStatus $status)
    {
        $this->status = $status;
    }

    public function registerInitialization(string $name, AbstractInitialization $initialization, array $dependencies = []): void
    {
        $this->initializations[$name] = $initialization;
        $this->dependencies[$name] = $dependencies;

        foreach ($dependencies as $dependency) {
            $this->status->addDependency($dependency);
        }
    }

    public function hasInitialization(string $name): bool
    {
        return isset($this->initializations[$name]);
    }

    public function getInitialization(string $name): ?AbstractInitialization
    {
        return $this->initializations[$name] ?? null;
    }

    public function getDependencies(string $name): array
    {
        return $this->dependencies[$name] ?? [];
    }

    public function hasDependencies(string $name): bool
    {
        return !empty($this->dependencies[$name]);
    }

    public function isInitializationComplete(string $name): bool
    {
        $initialization = $this->getInitialization($name);
        return $initialization !== null && $initialization->getStatus()->isInitialized();
    }

    public function initialize(string $name): void
    {
        $initialization = $this->getInitialization($name);
        if ($initialization === null) {
            throw new \RuntimeException("Initialization '{$name}' not found");
        }

        // Check dependencies
        foreach ($this->getDependencies($name) as $dependency) {
            if (!$this->isInitializationComplete($dependency)) {
                throw new \RuntimeException("Dependency '{$dependency}' not initialized");
            }
        }

        try {
            $initialization->validateConfiguration();
            $initialization->testConnection();
            $initialization->performInitialization();
        } catch (\Throwable $e) {
            $initialization->getStatus()->addError($e->getMessage());
            throw $e;
        }
    }

    public function addDependency(string $name, string $dependency): void
    {
        if (!isset($this->dependencies[$name])) {
            $this->dependencies[$name] = [];
        }

        if (!in_array($dependency, $this->dependencies[$name])) {
            $this->dependencies[$name][] = $dependency;
            $this->checkCircularDependencies($name, [$name]);
        }
    }

    private function checkCircularDependencies(string $name, array $chain): void
    {
        foreach ($this->getDependencies($name) as $dependency) {
            if (in_array($dependency, $chain)) {
                throw new CircularDependencyException($chain);
            }

            $newChain = array_merge($chain, [$dependency]);
            $this->checkCircularDependencies($dependency, $newChain);
        }
    }

    public function getStatus(): InitializationStatus
    {
        return $this->status;
    }

    public function updateState(InitializationStatus $status): void
    {
        $this->status = $status;
    }

    public function getState(): InitializationStatus
    {
        return $this->status;
    }

    public function isAllComplete(): bool
    {
        foreach ($this->initializations as $name => $initialization) {
            if (!$this->isInitializationComplete($name)) {
                return false;
            }
        }
        return true;
    }

    public function getInitializationOrder(): array
    {
        if (empty($this->initializationOrder)) {
            $this->resolveInitializationOrder();
        }
        return $this->initializationOrder;
    }

    private function resolveInitializationOrder(): void
    {
        $visited = [];
        $this->initializationOrder = [];

        foreach ($this->initializations as $name => $_) {
            if (!isset($visited[$name])) {
                $this->resolveDependencies($name, $visited);
            }
        }
    }

    private function resolveDependencies(string $name, array &$visited): void
    {
        $visited[$name] = true;

        foreach ($this->getDependencies($name) as $dependency) {
            if (!isset($visited[$dependency])) {
                $this->resolveDependencies($dependency, $visited);
            }
        }

        $this->initializationOrder[] = $name;
    }

    public function reset(): void
    {
        $this->status->reset();
        foreach ($this->initializations as $initialization) {
            $initialization->getStatus()->reset();
        }
    }
} 