<?php

namespace LegalStudy\ModularInitialization\Services;

use LegalStudy\ModularInitialization\Contracts\InitializationStatusInterface;
use InvalidArgumentException;

class InitializationStatus implements InitializationStatusInterface
{
    public const PENDING = 'pending';
    public const INITIALIZING = 'initializing';
    public const INITIALIZED = 'initialized';
    public const COMPLETE = 'complete';
    public const ERROR = 'error';
    public const FAILED = 'failed';

    private string $status = self::PENDING;
    private array $data = [];
    private array $errors = [];
    private array $warnings = [];
    private array $dependencies = [];
    private ?float $startTime = null;
    private ?float $endTime = null;

    public function __construct()
    {
        $this->startTiming();
    }

    public function startTiming(): void
    {
        $this->startTime = microtime(true);
    }

    public function endTiming(): void
    {
        $this->endTime = microtime(true);
    }

    public function setStatus(string $status): void
    {
        if (!in_array($status, [
            self::PENDING,
            self::INITIALIZING,
            self::INITIALIZED,
            self::COMPLETE,
            self::ERROR,
            self::FAILED
        ])) {
            throw new InvalidArgumentException("Invalid status: {$status}");
        }
        $this->status = $status;
    }

    public function getStatus(): string
    {
        return $this->status;
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

    public function setData(array $data): void
    {
        $this->data = $data;
    }

    public function addError(string $error): void
    {
        $this->errors[] = $error;
        if ($this->status !== self::FAILED) {
            $this->status = self::ERROR;
        }
    }

    public function getErrors(): array
    {
        return $this->errors;
    }

    public function setErrors(array $errors): void
    {
        $this->errors = $errors;
        if (!empty($errors) && $this->status !== self::FAILED) {
            $this->status = self::ERROR;
        }
    }

    public function addWarning(string $warning): void
    {
        $this->warnings[] = $warning;
    }

    public function getWarnings(): array
    {
        return $this->warnings;
    }

    public function markComplete(): void
    {
        $this->endTiming();
        $this->status = self::COMPLETE;
    }

    public function markFailed(): void
    {
        $this->endTiming();
        $this->status = self::FAILED;
    }

    public function getDuration(): ?float
    {
        if ($this->startTime === null || $this->endTime === null) {
            return null;
        }
        return $this->endTime - $this->startTime;
    }

    public function isPending(): bool
    {
        return $this->status === self::PENDING;
    }

    public function isInitializing(): bool
    {
        return $this->status === self::INITIALIZING;
    }

    public function isInitialized(): bool
    {
        return $this->status === self::INITIALIZED;
    }

    public function isComplete(): bool
    {
        return $this->status === self::COMPLETE;
    }

    public function isError(): bool
    {
        return $this->status === self::ERROR;
    }

    public function isFailed(): bool
    {
        return $this->status === self::FAILED;
    }

    public function isSuccess(): bool
    {
        return $this->status === self::COMPLETE || $this->status === self::INITIALIZED;
    }

    public function reset(): void
    {
        $this->status = self::PENDING;
        $this->data = [];
        $this->errors = [];
        $this->warnings = [];
        $this->startTime = null;
        $this->endTime = null;
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

    public function getStartTime(): ?float
    {
        return $this->startTime;
    }

    public function getEndTime(): ?float
    {
        return $this->endTime;
    }

    public function toArray(): array
    {
        return [
            'status' => $this->status,
            'data' => $this->data,
            'errors' => $this->errors,
            'warnings' => $this->warnings,
            'duration' => $this->getDuration(),
            'hasErrors' => !empty($this->errors),
            'hasWarnings' => !empty($this->warnings)
        ];
    }

    public function setInitialized(bool $initialized): void
    {
        if ($initialized) {
            $this->status = self::INITIALIZED;
        } else {
            $this->status = self::PENDING;
        }
    }
} 