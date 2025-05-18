<?php

namespace Tests\MCP;

use Psr\Log\AbstractLogger;
use Psr\Log\LogLevel;

class TestLogger extends AbstractLogger
{
    private array $logs = [];

    public function log($level, string|\Stringable $message, array $context = []): void
    {
        $this->logs[] = [
            'level' => $level,
            'message' => (string) $message,
            'context' => $context
        ];
    }

    public function hasInfo(string $message): bool
    {
        return $this->hasLog(LogLevel::INFO, $message);
    }

    public function hasError(string $message): bool
    {
        return $this->hasLog(LogLevel::ERROR, $message);
    }

    private function hasLog(string $level, string $message): bool
    {
        foreach ($this->logs as $log) {
            if ($log['level'] === $level && $log['message'] === $message) {
                return true;
            }
        }
        return false;
    }

    public function getLogs(): array
    {
        return $this->logs;
    }

    public function clear(): void
    {
        $this->logs = [];
    }
} 