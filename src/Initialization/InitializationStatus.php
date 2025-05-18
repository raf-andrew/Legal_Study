<?php

namespace LegalStudy\Initialization;

class InitializationStatus
{
    public const PENDING = 'pending';
    public const INITIALIZING = 'initializing';
    public const INITIALIZED = 'initialized';
    public const FAILED = 'failed';
    public const ERROR = 'error';
    public const COMPLETE = 'complete';
    public const INCOMPLETE = 'incomplete';
    public const UNKNOWN = 'unknown';

    private string $status = self::PENDING;
    private array $data = [];
    private array $errors = [];
    private array $warnings = [];
    private ?float $startTime = null;
    private ?float $endTime = null;

    public function __construct()
    {
        $this->startTime = null;
        $this->endTime = null;
    }

    public function getStatus(): string
    {
        return $this->status;
    }

    public function setStatus(string $status): void
    {
        if (!in_array($status, [
            self::PENDING,
            self::INITIALIZING,
            self::INITIALIZED,
            self::FAILED,
            self::ERROR,
            self::COMPLETE,
            self::INCOMPLETE,
            self::UNKNOWN
        ])) {
            throw new \InvalidArgumentException("Invalid status: {$status}");
        }
        $this->status = $status;
    }

    public function getData(): array
    {
        return $this->data;
    }

    public function setData(array $data): void
    {
        $this->data = $data;
    }

    public function addData(string $key, mixed $value): void
    {
        $this->data[$key] = $value;
    }

    public function getErrors(): array
    {
        return $this->errors;
    }

    public function setErrors(array $errors): void
    {
        $this->errors = $errors;
    }

    public function addError(string $error): void
    {
        $this->errors[] = $error;
        $this->status = self::FAILED;
    }

    public function getWarnings(): array
    {
        return $this->warnings;
    }

    public function setWarnings(array $warnings): void
    {
        $this->warnings = $warnings;
    }

    public function addWarning(string $warning): void
    {
        $this->warnings[] = $warning;
    }

    public function isInitialized(): bool
    {
        return $this->status === self::INITIALIZED;
    }

    public function isFailed(): bool
    {
        return $this->status === self::FAILED;
    }

    public function isError(): bool
    {
        return $this->status === self::ERROR;
    }

    public function isPending(): bool
    {
        return $this->status === self::PENDING;
    }

    public function isInitializing(): bool
    {
        return $this->status === self::INITIALIZING;
    }

    public function isComplete(): bool
    {
        return $this->status === self::COMPLETE;
    }

    public function isIncomplete(): bool
    {
        return $this->status === self::INCOMPLETE;
    }

    public function isUnknown(): bool
    {
        return $this->status === self::UNKNOWN;
    }

    public function isSuccess(): bool
    {
        return $this->status === self::INITIALIZED || $this->status === self::COMPLETE;
    }

    public function hasErrors(): bool
    {
        return !empty($this->errors);
    }

    public function hasWarnings(): bool
    {
        return !empty($this->warnings);
    }

    public function markInitialized(): void
    {
        if ($this->status === self::FAILED) {
            throw new \RuntimeException('Cannot mark as initialized when status is failed');
        }
        if ($this->status === self::ERROR && !empty($this->errors)) {
            throw new \RuntimeException('Cannot mark as initialized when there are errors');
        }
        $this->status = self::INITIALIZED;
        $this->endTiming();
    }

    public function markFailed(): void
    {
        $this->status = self::FAILED;
        $this->endTiming();
    }

    public function markComplete(): void
    {
        if ($this->status === self::FAILED) {
            throw new \RuntimeException('Cannot mark as complete when status is failed');
        }
        if ($this->status === self::ERROR && !empty($this->errors)) {
            throw new \RuntimeException('Cannot mark as complete when there are errors');
        }
        $this->status = self::COMPLETE;
        $this->endTiming();
    }

    public function markIncomplete(): void
    {
        $this->status = self::INCOMPLETE;
        $this->endTiming();
    }

    public function startTiming(): void
    {
        $this->startTime = microtime(true);
    }

    public function endTiming(): void
    {
        $this->endTime = microtime(true);
    }

    public function getDuration(): ?float
    {
        if ($this->startTime === null || $this->endTime === null) {
            return null;
        }
        return $this->endTime - $this->startTime;
    }

    public function toArray(): array
    {
        return [
            'status' => $this->status,
            'data' => $this->data,
            'errors' => $this->errors,
            'warnings' => $this->warnings,
            'duration' => $this->getDuration(),
            'hasErrors' => $this->hasErrors(),
            'hasWarnings' => $this->hasWarnings()
        ];
    }
} 