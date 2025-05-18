<?php

namespace LegalStudy\Initialization;

class InitializationErrorDetector
{
    private array $errorPatterns = [];
    private array $errorHandlers = [];
    private array $errorHistory = [];

    public function registerErrorPattern(string $pattern, callable $handler): void
    {
        $this->errorPatterns[$pattern] = $handler;
    }

    public function registerErrorHandler(string $errorType, callable $handler): void
    {
        $this->errorHandlers[$errorType] = $handler;
    }

    public function detectError(string $component, \Throwable $error): void
    {
        $errorType = $this->determineErrorType($error);
        $errorData = [
            'component' => $component,
            'type' => $errorType,
            'message' => $error->getMessage(),
            'code' => $error->getCode(),
            'file' => $error->getFile(),
            'line' => $error->getLine(),
            'trace' => $error->getTrace(),
            'timestamp' => microtime(true)
        ];

        $this->errorHistory[] = $errorData;

        if (isset($this->errorHandlers[$errorType])) {
            $handler = $this->errorHandlers[$errorType];
            $handler($errorData);
        }
    }

    public function getErrorHistory(): array
    {
        return $this->errorHistory;
    }

    public function getErrorHistoryForComponent(string $component): array
    {
        return array_filter($this->errorHistory, function($error) use ($component) {
            return $error['component'] === $component;
        });
    }

    public function getErrorCount(): int
    {
        return count($this->errorHistory);
    }

    public function getErrorCountForComponent(string $component): int
    {
        return count($this->getErrorHistoryForComponent($component));
    }

    public function clearErrorHistory(): void
    {
        $this->errorHistory = [];
    }

    private function determineErrorType(\Throwable $error): string
    {
        foreach ($this->errorPatterns as $pattern => $handler) {
            if (preg_match($pattern, $error->getMessage())) {
                return $handler($error);
            }
        }

        return get_class($error);
    }

    public function hasErrors(): bool
    {
        return !empty($this->errorHistory);
    }

    public function hasErrorsForComponent(string $component): bool
    {
        return $this->getErrorCountForComponent($component) > 0;
    }

    public function getLastError(): ?array
    {
        return end($this->errorHistory) ?: null;
    }

    public function getLastErrorForComponent(string $component): ?array
    {
        $componentErrors = $this->getErrorHistoryForComponent($component);
        return end($componentErrors) ?: null;
    }
} 