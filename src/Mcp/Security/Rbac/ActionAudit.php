<?php

namespace Mcp\Security\Rbac;

class ActionAudit
{
    private array $auditLog;
    private int $maxLogSize;

    public function __construct(int $maxLogSize = 1000)
    {
        $this->auditLog = [];
        $this->maxLogSize = $maxLogSize;
    }

    public function logAction(
        string $roleName,
        string $action,
        array $details = [],
        ?string $result = null,
        ?string $error = null
    ): void {
        $logEntry = [
            'timestamp' => microtime(true),
            'role' => $roleName,
            'action' => $action,
            'details' => $details,
            'result' => $result,
            'error' => $error
        ];

        $this->auditLog[] = $logEntry;

        // Maintain log size limit
        if (count($this->auditLog) > $this->maxLogSize) {
            array_shift($this->auditLog);
        }
    }

    public function getAuditLog(
        ?string $roleName = null,
        ?string $action = null,
        ?float $startTime = null,
        ?float $endTime = null
    ): array {
        return array_values(array_filter($this->auditLog, function($entry) use ($roleName, $action, $startTime, $endTime) {
            if ($roleName !== null && $entry['role'] !== $roleName) {
                return false;
            }
            if ($action !== null && $entry['action'] !== $action) {
                return false;
            }
            if ($startTime !== null && $entry['timestamp'] < $startTime) {
                return false;
            }
            if ($endTime !== null && $entry['timestamp'] > $endTime) {
                return false;
            }
            return true;
        }));
    }

    public function clearAuditLog(): void
    {
        $this->auditLog = [];
    }

    public function getMaxLogSize(): int
    {
        return $this->maxLogSize;
    }

    public function setMaxLogSize(int $size): void
    {
        $this->maxLogSize = $size;
        while (count($this->auditLog) > $this->maxLogSize) {
            array_shift($this->auditLog);
        }
    }
} 