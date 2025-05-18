<?php

namespace Mcp\Tenant;

use Mcp\Logging\LoggerInterface;
use Mcp\Security\EncryptionInterface;

class Tenant implements TenantInterface
{
    private string $id;
    private string $name;
    private string $databaseConnection;
    private string $encryptionKey;
    private array $administrators;
    private array $billingInfo;
    private array $resourceUsage;
    private bool $active;
    private \DateTime $createdAt;
    private \DateTime $lastActivity;
    private array $auditLog;
    private LoggerInterface $logger;
    private EncryptionInterface $encryption;

    public function __construct(
        string $id,
        string $name,
        LoggerInterface $logger,
        EncryptionInterface $encryption
    ) {
        $this->id = $id;
        $this->name = $name;
        $this->logger = $logger;
        $this->encryption = $encryption;
        $this->initialize();
    }

    private function initialize(): void
    {
        $this->databaseConnection = "tenant_{$this->id}";
        $this->encryptionKey = $this->encryption->generateKey();
        $this->administrators = [];
        $this->billingInfo = [
            'plan' => 'basic',
            'billing_cycle' => 'monthly',
            'payment_method' => null
        ];
        $this->resourceUsage = [
            'storage' => 0,
            'bandwidth' => 0,
            'api_calls' => 0
        ];
        $this->active = true;
        $this->createdAt = new \DateTime();
        $this->lastActivity = new \DateTime();
        $this->auditLog = [];
    }

    public function getId(): string
    {
        return $this->id;
    }

    public function getName(): string
    {
        return $this->name;
    }

    public function getDatabaseConnection(): string
    {
        return $this->databaseConnection;
    }

    public function getEncryptionKey(): string
    {
        return $this->encryptionKey;
    }

    public function getAdministrators(): array
    {
        return $this->administrators;
    }

    public function getBillingInfo(): array
    {
        return $this->billingInfo;
    }

    public function getResourceUsage(): array
    {
        return $this->resourceUsage;
    }

    public function isActive(): bool
    {
        return $this->active;
    }

    public function getCreatedAt(): \DateTime
    {
        return $this->createdAt;
    }

    public function getLastActivity(): \DateTime
    {
        return $this->lastActivity;
    }

    public function updateLastActivity(): void
    {
        $this->lastActivity = new \DateTime();
        $this->logAuditEntry('activity_update', [
            'timestamp' => $this->lastActivity->format('Y-m-d H:i:s')
        ]);
    }

    public function getAuditLog(): array
    {
        return $this->auditLog;
    }

    public function logAuditEntry(string $action, array $details): void
    {
        $entry = [
            'timestamp' => date('Y-m-d H:i:s'),
            'action' => $action,
            'details' => $details
        ];

        $this->auditLog[] = $entry;
        $this->logger->info("Tenant audit: {$action}", [
            'tenant_id' => $this->id,
            'details' => $details
        ]);
    }

    public function addAdministrator(string $userId, array $permissions): void
    {
        $this->administrators[$userId] = $permissions;
        $this->logAuditEntry('admin_added', [
            'user_id' => $userId,
            'permissions' => $permissions
        ]);
    }

    public function removeAdministrator(string $userId): void
    {
        if (isset($this->administrators[$userId])) {
            unset($this->administrators[$userId]);
            $this->logAuditEntry('admin_removed', [
                'user_id' => $userId
            ]);
        }
    }

    public function updateBillingInfo(array $info): void
    {
        $this->billingInfo = array_merge($this->billingInfo, $info);
        $this->logAuditEntry('billing_updated', [
            'changes' => $info
        ]);
    }

    public function updateResourceUsage(array $usage): void
    {
        $this->resourceUsage = array_merge($this->resourceUsage, $usage);
        $this->logAuditEntry('resource_usage_updated', [
            'usage' => $usage
        ]);
    }

    public function deactivate(): void
    {
        $this->active = false;
        $this->logAuditEntry('tenant_deactivated', [
            'timestamp' => date('Y-m-d H:i:s')
        ]);
    }

    public function activate(): void
    {
        $this->active = true;
        $this->logAuditEntry('tenant_activated', [
            'timestamp' => date('Y-m-d H:i:s')
        ]);
    }
} 