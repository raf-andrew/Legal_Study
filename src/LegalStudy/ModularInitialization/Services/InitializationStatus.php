<?php

namespace LegalStudy\ModularInitialization\Services;

class InitializationStatus
{
    private bool $initialized = false;
    private bool $failed = false;
    private array $errors = [];
    private array $data = [];
    private array $dependencies = [];

    public function isInitialized(): bool
    {
        return $this->initialized;
    }

    public function setInitialized(bool $initialized): void
    {
        $this->initialized = $initialized;
    }

    public function isFailed(): bool
    {
        return $this->failed;
    }

    public function addError(string $error): void
    {
        $this->errors[] = $error;
        $this->failed = true;
        
        // Log error
        $timestamp = date('Y-m-d_H-i-s');
        if (!is_dir('.errors')) {
            mkdir('.errors', 0755, true);
        }
        file_put_contents(".errors/{$timestamp}.log", $error . PHP_EOL, FILE_APPEND);
    }

    public function getErrors(): array
    {
        return $this->errors;
    }

    public function addData(string $key, mixed $value): void
    {
        $this->data[$key] = $value;
    }

    public function getData(string $key): mixed
    {
        return $this->data[$key] ?? null;
    }

    public function getAllData(): array
    {
        return $this->data;
    }

    public function addDependency(string $dependency): void
    {
        if (!in_array($dependency, $this->dependencies)) {
            $this->dependencies[] = $dependency;
        }
    }

    public function getDependencies(): array
    {
        return $this->dependencies;
    }

    public function reset(): void
    {
        $this->initialized = false;
        $this->failed = false;
        $this->errors = [];
        $this->data = [];
        $this->dependencies = [];
    }
} 