<?php

namespace LegalStudy\Initialization;

class InitializationStatus
{
    public const PENDING = 'pending';
    public const INITIALIZING = 'initializing';
    public const INITIALIZED = 'initialized';
    public const COMPLETE = 'complete';
    public const FAILED = 'failed';

    private string $status = self::PENDING;
    private array $errors = [];
    private array $warnings = [];
    private array $data = [];
    private array $timings = [];

    public function getStatus(): string
    {
        return $this->status;
    }

    public function setStatus(string $status): void
    {
        $this->status = $status;
    }

    public function isPending(): bool
    {
        return $this->status === self::PENDING;
    }

    public function isComplete(): bool
    {
        return $this->status === self::COMPLETE;
    }

    public function hasErrors(): bool
    {
        return !empty($this->errors);
    }

    public function hasWarnings(): bool
    {
        return !empty($this->warnings);
    }

    public function getErrors(): array
    {
        return $this->errors;
    }

    public function getWarnings(): array
    {
        return $this->warnings;
    }

    public function getData(): array
    {
        return $this->data;
    }

    public function addError(string $error): void
    {
        $this->errors[] = $error;
        $this->status = self::FAILED;
    }

    public function addWarning(string $warning): void
    {
        $this->warnings[] = $warning;
    }

    public function setData(array $data): void
    {
        $this->data = $data;
    }

    public function markInitialized(): void
    {
        $this->status = self::INITIALIZED;
    }

    public function markComplete(): void
    {
        $this->status = self::COMPLETE;
    }

    public function markFailed(): void
    {
        $this->status = self::FAILED;
    }

    public function startTiming(string $operation): void
    {
        $this->timings[$operation] = [
            'start' => microtime(true),
            'end' => null,
            'duration' => null
        ];
    }

    public function endTiming(string $operation): void
    {
        if (isset($this->timings[$operation])) {
            $this->timings[$operation]['end'] = microtime(true);
            $this->timings[$operation]['duration'] = 
                $this->timings[$operation]['end'] - $this->timings[$operation]['start'];
        }
    }

    public function getTimings(): array
    {
        return $this->timings;
    }
} 