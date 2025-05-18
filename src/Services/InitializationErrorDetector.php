<?php

namespace LegalStudy\ModularInitialization\Services;

class InitializationErrorDetector
{
    private array $errorPatterns = [];
    private array $errorHistory = [];
    private array $errorHandlers = [];

    public function registerErrorPattern(string $component, string $pattern): void
    {
        if (!isset($this->errorPatterns[$component])) {
            $this->errorPatterns[$component] = [];
        }
        $this->errorPatterns[$component][] = $pattern;
    }

    public function registerErrorHandler(string $component, callable $handler): void
    {
        $this->errorHandlers[$component] = $handler;
    }

    public function detectError(string $component, string $message): bool
    {
        if (!isset($this->errorPatterns[$component])) {
            return false;
        }

        foreach ($this->errorPatterns[$component] as $pattern) {
            if (preg_match($pattern, $message)) {
                $this->addError($component, $message);
                if (isset($this->errorHandlers[$component])) {
                    call_user_func($this->errorHandlers[$component], $message);
                }
                return true;
            }
        }

        return false;
    }

    public function addError(string $component, string $message): void
    {
        if (!isset($this->errorHistory[$component])) {
            $this->errorHistory[$component] = [];
        }
        $this->errorHistory[$component][] = [
            'message' => $message,
            'timestamp' => microtime(true)
        ];
    }

    public function getErrorCount(?string $component = null): int
    {
        if ($component === null) {
            $count = 0;
            foreach ($this->errorHistory as $errors) {
                $count += count($errors);
            }
            return $count;
        }
        return isset($this->errorHistory[$component]) ? count($this->errorHistory[$component]) : 0;
    }

    public function hasErrors(?string $component = null): bool
    {
        if ($component === null) {
            return !empty($this->errorHistory);
        }
        return isset($this->errorHistory[$component]) && !empty($this->errorHistory[$component]);
    }

    public function getLastError(?string $component = null): ?array
    {
        if ($component === null) {
            $lastError = null;
            $lastTimestamp = 0;
            foreach ($this->errorHistory as $errors) {
                foreach ($errors as $error) {
                    if ($error['timestamp'] > $lastTimestamp) {
                        $lastError = $error;
                        $lastTimestamp = $error['timestamp'];
                    }
                }
            }
            return $lastError;
        }

        if (!isset($this->errorHistory[$component]) || empty($this->errorHistory[$component])) {
            return null;
        }

        return end($this->errorHistory[$component]);
    }

    public function getErrorHistory(?string $component = null): array
    {
        if ($component === null) {
            return $this->errorHistory;
        }
        return $this->errorHistory[$component] ?? [];
    }

    public function clearErrorHistory(?string $component = null): void
    {
        if ($component === null) {
            $this->errorHistory = [];
        } else {
            $this->errorHistory[$component] = [];
        }
    }

    public function getErrorPatterns(string $component): array
    {
        return $this->errorPatterns[$component] ?? [];
    }

    public function hasErrorHandler(string $component): bool
    {
        return isset($this->errorHandlers[$component]);
    }
} 