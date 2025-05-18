<?php

namespace LegalStudy\ModularInitialization;

use LegalStudy\ModularInitialization\Services\InitializationStatus;

abstract class AbstractInitialization
{
    protected InitializationStatus $status;
    protected array $config = [];

    public function __construct(InitializationStatus $status)
    {
        $this->status = $status;
    }

    public function validateConfiguration(array $config = []): void
    {
        $this->config = $config;
        if (!$this->doValidateConfiguration()) {
            throw new \RuntimeException('Configuration validation failed');
        }
    }

    public function testConnection(): bool
    {
        if (!$this->doTestConnection()) {
            throw new \RuntimeException('Connection test failed');
        }
        return true;
    }

    public function performInitialization(): void
    {
        try {
            $this->doPerformInitialization();
        } catch (\Throwable $e) {
            $this->status->addError($e->getMessage());
            throw $e;
        }
    }

    public function getStatus(): InitializationStatus
    {
        return $this->status;
    }

    public function getConfig(): array
    {
        return $this->config;
    }

    abstract protected function doValidateConfiguration(): bool;
    abstract protected function doTestConnection(): bool;
    abstract protected function doPerformInitialization(): void;
} 