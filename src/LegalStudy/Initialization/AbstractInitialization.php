<?php

namespace LegalStudy\Initialization;

abstract class AbstractInitialization
{
    protected InitializationStatus $status;
    protected InitializationPerformanceMonitor $performanceMonitor;
    protected array $config = [];

    public function __construct()
    {
        $this->status = new InitializationStatus();
        $this->performanceMonitor = new InitializationPerformanceMonitor();
    }

    public function getStatus(): InitializationStatus
    {
        return $this->status;
    }

    public function setStatus(InitializationStatus $status): void
    {
        $this->status = $status;
    }

    public function validateConfiguration(array $config): bool
    {
        $this->status->startTiming('validate_configuration');
        $result = $this->doValidateConfiguration($config);
        
        if ($result) {
            $this->config = $config;
        } else {
            $this->status->markFailed();
            $this->status->addError('Configuration validation failed');
            throw new \RuntimeException('Configuration validation failed');
        }
        
        return $result;
    }

    public function testConnection(): bool
    {
        $this->performanceMonitor->startMeasurement('test_connection');
        $result = $this->doTestConnection();
        $this->performanceMonitor->endMeasurement('test_connection');
        
        if (!$result) {
            $this->status->markFailed();
            $this->status->addError('Connection test failed');
            throw new \RuntimeException('Connection test failed');
        }
        
        return $result;
    }

    public function performInitialization(): void
    {
        $this->performanceMonitor->startMeasurement('initialization');
        
        try {
            $this->doPerformInitialization();
            $this->status->markInitialized();
        } catch (\Exception $e) {
            $this->status->markFailed();
            $this->status->addError($e->getMessage());
            throw $e;
        } finally {
            $this->performanceMonitor->endMeasurement('initialization');
        }
    }

    public function getConfig(): array
    {
        return $this->config;
    }

    protected function addError(string $error): void
    {
        $this->status->addError($error);
    }

    protected function addWarning(string $warning): void
    {
        $this->status->addWarning($warning);
    }

    protected function markComplete(): void
    {
        $this->status->markComplete();
    }

    // Test helper methods
    public function testAddError(string $error): void
    {
        $this->addError($error);
    }

    public function testAddWarning(string $warning): void
    {
        $this->addWarning($warning);
    }

    public function testMarkComplete(): void
    {
        $this->markComplete();
    }

    abstract protected function doValidateConfiguration(array $config): bool;
    abstract protected function doTestConnection(): bool;
    abstract protected function doPerformInitialization(): void;
} 