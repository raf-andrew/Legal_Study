<?php

namespace Mcp\Agent;

use Mcp\Logging\LoggerInterface;
use Mcp\Security\PermissionManagerInterface;

abstract class AbstractAgent implements AgentInterface
{
    protected array $config = [];
    protected array $status = [];
    protected array $auditLog = [];
    protected array $requiredPermissions = [];
    protected LoggerInterface $logger;
    protected PermissionManagerInterface $permissionManager;

    public function __construct(
        LoggerInterface $logger,
        PermissionManagerInterface $permissionManager
    ) {
        $this->logger = $logger;
        $this->permissionManager = $permissionManager;
        $this->initialize([]);
    }

    public function initialize(array $config): void
    {
        $this->config = array_merge($this->getDefaultConfig(), $config);
        $this->status = [
            'initialized' => true,
            'last_execution' => null,
            'error_count' => 0,
            'success_count' => 0
        ];
    }

    public function getStatus(): array
    {
        return $this->status;
    }

    public function handleError(\Throwable $error): void
    {
        $this->status['error_count']++;
        $this->logger->error('Agent error: ' . $error->getMessage(), [
            'agent' => static::class,
            'error' => $error
        ]);
        $this->logAuditEntry('error', [
            'message' => $error->getMessage(),
            'trace' => $error->getTraceAsString()
        ]);
    }

    public function getRequiredPermissions(): array
    {
        return $this->requiredPermissions;
    }

    public function hasRequiredPermissions(): bool
    {
        return $this->permissionManager->hasPermissions($this->requiredPermissions);
    }

    public function getAuditLog(): array
    {
        return $this->auditLog;
    }

    public function logAuditEntry(string $action, array $details): void
    {
        $this->auditLog[] = [
            'timestamp' => date('Y-m-d H:i:s'),
            'action' => $action,
            'details' => $details
        ];
    }

    protected function getDefaultConfig(): array
    {
        return [
            'enabled' => true,
            'max_retries' => 3,
            'timeout' => 30,
            'log_level' => 'info'
        ];
    }

    protected function updateStatus(array $updates): void
    {
        $this->status = array_merge($this->status, $updates);
    }

    protected function validatePermissions(): void
    {
        if (!$this->hasRequiredPermissions()) {
            throw new \RuntimeException('Agent does not have required permissions');
        }
    }
} 