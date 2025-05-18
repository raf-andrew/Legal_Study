<?php

namespace LegalStudy\ModularInitialization\Tests\Initialization;

use LegalStudy\ModularInitialization\AbstractInitialization;
use LegalStudy\ModularInitialization\Services\InitializationStatus;

class TestInitialization extends AbstractInitialization
{
    private bool $shouldFail = false;
    private bool $shouldFailValidation = false;
    private bool $shouldFailConnection = false;

    public function __construct(InitializationStatus $status)
    {
        parent::__construct($status);
    }

    public function setShouldFail(bool $shouldFail): void
    {
        $this->shouldFail = $shouldFail;
    }

    public function setShouldFailValidation(bool $shouldFailValidation): void
    {
        $this->shouldFailValidation = $shouldFailValidation;
    }

    public function setShouldFailConnection(bool $shouldFailConnection): void
    {
        $this->shouldFailConnection = $shouldFailConnection;
    }

    protected function doValidateConfiguration(): bool
    {
        if ($this->shouldFailValidation) {
            $this->getStatus()->addError('Validation failed');
            return false;
        }
        return true;
    }

    protected function doTestConnection(): bool
    {
        if ($this->shouldFailConnection) {
            $this->getStatus()->addError('Connection test failed');
            return false;
        }
        return true;
    }

    protected function doPerformInitialization(): void
    {
        if ($this->shouldFail) {
            throw new \RuntimeException('Initialization failed');
        }
        $this->getStatus()->setInitialized(true);
    }
} 