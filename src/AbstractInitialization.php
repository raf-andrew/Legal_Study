<?php

namespace LegalStudy\ModularInitialization;

use LegalStudy\ModularInitialization\Services\InitializationStatus;
use LegalStudy\ModularInitialization\Services\InitializationPerformanceMonitor;
use Exception;

abstract class AbstractInitialization
{
    protected array $config = [];
    protected InitializationStatus $status;
    protected InitializationPerformanceMonitor $performanceMonitor;

    public function __construct()
    {
        $this->status = new InitializationStatus();
        $this->performanceMonitor = new InitializationPerformanceMonitor();
    }

    public function validateConfiguration(): void
    {
        $this->performanceMonitor->startMeasurement(static::class, 'validateConfiguration');
        try {
            $this->doValidateConfiguration();
        } catch (Exception $e) {
            $this->addError($e->getMessage());
            throw $e;
        } finally {
            $this->performanceMonitor->endMeasurement(static::class, 'validateConfiguration');
        }
    }

    public function testConnection(): bool
    {
        $this->performanceMonitor->startMeasurement(static::class, 'testConnection');
        try {
            return $this->doTestConnection();
        } catch (Exception $e) {
            $this->addError($e->getMessage());
            return false;
        } finally {
            $this->performanceMonitor->endMeasurement(static::class, 'testConnection');
        }
    }

    public function performInitialization(): void
    {
        $this->performanceMonitor->startMeasurement(static::class, 'performInitialization');
        try {
            $this->doPerformInitialization();
            $this->status->markComplete();
        } catch (Exception $e) {
            $this->addError($e->getMessage());
            $this->status->markFailed();
            throw $e;
        } finally {
            $this->performanceMonitor->endMeasurement(static::class, 'performInitialization');
        }
    }

    public function setConfiguration(array $config): void
    {
        $this->config = $config;
    }

    public function getConfiguration(): array
    {
        return $this->config;
    }

    public function getStatus(): InitializationStatus
    {
        return $this->status;
    }

    public function getPerformanceMonitor(): InitializationPerformanceMonitor
    {
        return $this->performanceMonitor;
    }

    protected function addError(string $error): void
    {
        $this->status->addError($error);
    }

    protected function addWarning(string $warning): void
    {
        $this->status->addWarning($warning);
    }

    protected function addData(string $key, mixed $value): void
    {
        $this->status->addData($key, $value);
    }

    abstract protected function doValidateConfiguration(): void;
    abstract protected function doTestConnection(): bool;
    abstract protected function doPerformInitialization(): void;
} 