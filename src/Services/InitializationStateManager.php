<?php

namespace LegalStudy\ModularInitialization\Services;

use LegalStudy\ModularInitialization\AbstractInitialization;
use LegalStudy\ModularInitialization\Initializers\DatabaseInitialization;
use LegalStudy\ModularInitialization\Initializers\CacheInitialization;
use LegalStudy\ModularInitialization\Initializers\ExternalApiInitialization;
use LegalStudy\ModularInitialization\Initializers\FileSystemInitialization;
use LegalStudy\ModularInitialization\Initializers\NetworkInitialization;
use LegalStudy\ModularInitialization\Initializers\QueueInitialization;

class InitializationStateManager
{
    private array $initializers = [];
    private InitializationStatus $status;
    private bool $isInitialized = false;

    public function __construct()
    {
        $this->status = new InitializationStatus();
    }

    public function addInitializer(AbstractInitialization $initializer): void
    {
        $this->initializers[] = $initializer;
    }

    public function initialize(): void
    {
        if ($this->isInitialized) {
            return;
        }

        try {
            // Validate configurations
            foreach ($this->initializers as $initializer) {
                $initializer->validateConfiguration();
            }

            // Test connections
            foreach ($this->initializers as $initializer) {
                if (!$initializer->testConnection()) {
                    throw new \RuntimeException("Connection test failed for " . get_class($initializer));
                }
            }

            // Perform initialization
            foreach ($this->initializers as $initializer) {
                $initializer->performInitialization();
            }

            $this->isInitialized = true;
            $this->status->setInitialized(true);
        } catch (\Exception $e) {
            $this->status->addError($e->getMessage());
            throw $e;
        }
    }

    public function getStatus(): InitializationStatus
    {
        return $this->status;
    }

    public function isInitialized(): bool
    {
        return $this->isInitialized;
    }

    public function getInitializer(string $class): ?AbstractInitialization
    {
        foreach ($this->initializers as $initializer) {
            if (get_class($initializer) === $class) {
                return $initializer;
            }
        }
        return null;
    }

    public function getDatabaseInitializer(): ?DatabaseInitialization
    {
        return $this->getInitializer(DatabaseInitialization::class);
    }

    public function getCacheInitializer(): ?CacheInitialization
    {
        return $this->getInitializer(CacheInitialization::class);
    }

    public function getExternalApiInitializer(): ?ExternalApiInitialization
    {
        return $this->getInitializer(ExternalApiInitialization::class);
    }

    public function getFileSystemInitializer(): ?FileSystemInitialization
    {
        return $this->getInitializer(FileSystemInitialization::class);
    }

    public function getNetworkInitializer(): ?NetworkInitialization
    {
        return $this->getInitializer(NetworkInitialization::class);
    }

    public function getQueueInitializer(): ?QueueInitialization
    {
        return $this->getInitializer(QueueInitialization::class);
    }

    public function reset(): void
    {
        $this->initializers = [];
        $this->status = new InitializationStatus();
        $this->isInitialized = false;
    }
} 