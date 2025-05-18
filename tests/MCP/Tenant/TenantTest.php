<?php

namespace Tests\Mcp\Tenant;

use Mcp\Tenant\Tenant;
use Mcp\Tenant\TenantInterface;
use Mcp\Logging\LoggerInterface;
use Mcp\Security\EncryptionInterface;
use PHPUnit\Framework\TestCase;

class TenantTest extends TestCase
{
    private LoggerInterface $logger;
    private EncryptionInterface $encryption;
    private Tenant $tenant;

    protected function setUp(): void
    {
        $this->logger = $this->createMock(LoggerInterface::class);
        $this->encryption = $this->createMock(EncryptionInterface::class);
        
        $this->encryption->method('generateKey')
            ->willReturn('test_encryption_key');

        $this->tenant = new Tenant(
            'test_tenant',
            'Test Tenant',
            $this->logger,
            $this->encryption
        );
    }

    public function testTenantImplementsInterface(): void
    {
        $this->assertInstanceOf(TenantInterface::class, $this->tenant);
    }

    public function testTenantInitialization(): void
    {
        $this->assertEquals('test_tenant', $this->tenant->getId());
        $this->assertEquals('Test Tenant', $this->tenant->getName());
        $this->assertEquals('tenant_test_tenant', $this->tenant->getDatabaseConnection());
        $this->assertEquals('test_encryption_key', $this->tenant->getEncryptionKey());
        $this->assertTrue($this->tenant->isActive());
    }

    public function testTenantAdministratorManagement(): void
    {
        $userId = 'admin1';
        $permissions = ['read', 'write'];

        $this->tenant->addAdministrator($userId, $permissions);
        $admins = $this->tenant->getAdministrators();

        $this->assertArrayHasKey($userId, $admins);
        $this->assertEquals($permissions, $admins[$userId]);

        $this->tenant->removeAdministrator($userId);
        $admins = $this->tenant->getAdministrators();

        $this->assertArrayNotHasKey($userId, $admins);
    }

    public function testTenantBillingInfo(): void
    {
        $billingInfo = [
            'plan' => 'premium',
            'payment_method' => 'credit_card'
        ];

        $this->tenant->updateBillingInfo($billingInfo);
        $currentBillingInfo = $this->tenant->getBillingInfo();

        $this->assertEquals('premium', $currentBillingInfo['plan']);
        $this->assertEquals('credit_card', $currentBillingInfo['payment_method']);
    }

    public function testTenantResourceUsage(): void
    {
        $usage = [
            'storage' => 1024,
            'api_calls' => 1000
        ];

        $this->tenant->updateResourceUsage($usage);
        $currentUsage = $this->tenant->getResourceUsage();

        $this->assertEquals(1024, $currentUsage['storage']);
        $this->assertEquals(1000, $currentUsage['api_calls']);
    }

    public function testTenantActivationState(): void
    {
        $this->assertTrue($this->tenant->isActive());

        $this->tenant->deactivate();
        $this->assertFalse($this->tenant->isActive());

        $this->tenant->activate();
        $this->assertTrue($this->tenant->isActive());
    }

    public function testTenantAuditLogging(): void
    {
        $action = 'test_action';
        $details = ['test' => 'value'];

        $this->tenant->logAuditEntry($action, $details);
        $auditLog = $this->tenant->getAuditLog();

        $this->assertCount(1, $auditLog);
        $this->assertEquals($action, $auditLog[0]['action']);
        $this->assertEquals($details, $auditLog[0]['details']);
    }

    public function testTenantLastActivity(): void
    {
        $initialActivity = $this->tenant->getLastActivity();
        sleep(1);
        $this->tenant->updateLastActivity();
        $newActivity = $this->tenant->getLastActivity();

        $this->assertGreaterThan($initialActivity, $newActivity);
    }
} 