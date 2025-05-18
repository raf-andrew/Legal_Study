<?php

namespace LegalStudy\Initialization;

abstract class AbstractInitialization implements InitializationInterface
{
    protected InitializationStatus $status;
    protected array $config;
    protected InitializationPerformanceMonitor $performanceMonitor;

    public function __construct()
    {
        $this->status = new InitializationStatus();
        $this->performanceMonitor = new InitializationPerformanceMonitor();
    }

    public function validateConfiguration(array $config): void
    {
        $this->config = $config;
        $this->status->startTiming();
        
        try {
            if (!$this->doValidateConfiguration($config)) {
                $this->status->markFailed();
                throw new \RuntimeException('Configuration validation failed: ' . implode(', ', $this->status->getErrors()));
            }
        } catch (\Exception $e) {
            $this->status->addError($e->getMessage());
            $this->status->markFailed();
            throw $e;
        }
    }

    public function getStatus(): InitializationStatus
    {
        return $this->status;
    }

    public function setStatus(InitializationStatus $status): void
    {
        $this->status = $status;
    }

    public function testConnection(): bool
    {
        $this->performanceMonitor->startMeasurement(static::class, 'connection_test');
        try {
            $result = $this->doTestConnection();
            if (!$result) {
                $this->status->markFailed();
                throw new \RuntimeException('Connection test failed');
            }
            return $result;
        } finally {
            $this->performanceMonitor->endMeasurement(static::class, 'connection_test');
        }
    }

    public function performInitialization(): void
    {
        try {
            $this->performanceMonitor->startMeasurement(static::class, 'initialization');
            $this->doPerformInitialization();
            $this->performanceMonitor->endMeasurement(static::class, 'initialization');
            $this->status->markInitialized();
        } catch (\Exception $e) {
            $this->status->addError($e->getMessage());
            $this->status->markFailed();
            throw $e;
        }
    }

    protected function addError(string $message): void
    {
        $this->status->addError($message);
    }

    protected function addData(string $key, mixed $value): void
    {
        $this->status->addData($key, $value);
    }

    protected function addWarning(string $message): void
    {
        $this->status->addWarning($message);
    }

    protected function markComplete(): void
    {
        $this->status->markComplete();
    }

    public function setConfig(array $config): void
    {
        $this->config = $config;
    }

    public function getConfig(): array
    {
        return $this->config;
    }

    abstract protected function doValidateConfiguration(array $config): bool;
    abstract protected function doTestConnection(): bool;
    abstract protected function doPerformInitialization(): void;

    /**
     * For testing purposes only
     */
    public function testAddError(string $error): void
    {
        $this->addError($error);
    }

    /**
     * For testing purposes only
     */
    public function testAddWarning(string $warning): void
    {
        $this->addWarning($warning);
    }

    /**
     * For testing purposes only
     */
    public function testAddData(string $key, mixed $value): void
    {
        $this->addData($key, $value);
    }

    /**
     * For testing purposes only
     */
    public function testMarkComplete(): void
    {
        $this->markComplete();
    }
} 