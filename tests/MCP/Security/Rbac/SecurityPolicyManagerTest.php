<?php

namespace Tests\Mcp\Security\Rbac;

use Mcp\Security\Rbac\RoleManager;
use Mcp\Security\Rbac\ActionAudit;
use Mcp\Security\Rbac\SecurityPolicyManager;
use PHPUnit\Framework\TestCase;

class SecurityPolicyManagerTest extends TestCase
{
    private RoleManager $roleManager;
    private ActionAudit $actionAudit;
    private SecurityPolicyManager $policyManager;

    protected function setUp(): void
    {
        $this->roleManager = new RoleManager();
        $this->actionAudit = new ActionAudit();
        $this->policyManager = new SecurityPolicyManager($this->roleManager, $this->actionAudit);
    }

    public function testAddPolicy(): void
    {
        $rules = [
            [
                'effect' => 'allow',
                'roles' => ['admin'],
                'actions' => ['read', 'write']
            ]
        ];

        $this->policyManager->addPolicy('test_policy', $rules);
        $policies = $this->policyManager->getPolicies();
        $this->assertArrayHasKey('test_policy', $policies);
        $this->assertEquals($rules, $policies['test_policy']['rules']);
        $this->assertTrue($policies['test_policy']['enabled']);
    }

    public function testRemovePolicy(): void
    {
        $this->policyManager->addPolicy('test_policy', []);
        $this->policyManager->removePolicy('test_policy');
        $policies = $this->policyManager->getPolicies();
        $this->assertArrayNotHasKey('test_policy', $policies);
    }

    public function testEnableDisablePolicy(): void
    {
        $this->policyManager->addPolicy('test_policy', []);
        $this->policyManager->disablePolicy('test_policy');
        $this->assertFalse($this->policyManager->isPolicyEnabled('test_policy'));
        
        $this->policyManager->enablePolicy('test_policy');
        $this->assertTrue($this->policyManager->isPolicyEnabled('test_policy'));
    }

    public function testEnforcePolicyWithRoleCondition(): void
    {
        $rules = [
            [
                'effect' => 'allow',
                'roles' => ['admin'],
                'actions' => ['read']
            ]
        ];

        $this->policyManager->addPolicy('test_policy', $rules);
        
        // Test with matching role
        $this->assertTrue($this->policyManager->enforcePolicy('admin', 'read'));
        
        // Test with non-matching role
        $this->assertFalse($this->policyManager->enforcePolicy('user', 'read'));
    }

    public function testEnforcePolicyWithActionCondition(): void
    {
        $rules = [
            [
                'effect' => 'allow',
                'roles' => ['admin'],
                'actions' => ['read']
            ]
        ];

        $this->policyManager->addPolicy('test_policy', $rules);
        
        // Test with matching action
        $this->assertTrue($this->policyManager->enforcePolicy('admin', 'read'));
        
        // Test with non-matching action
        $this->assertFalse($this->policyManager->enforcePolicy('admin', 'write'));
    }

    public function testEnforcePolicyWithContextCondition(): void
    {
        $rules = [
            [
                'effect' => 'allow',
                'roles' => ['admin'],
                'actions' => ['read'],
                'conditions' => ['resource' => 'public']
            ]
        ];

        $this->policyManager->addPolicy('test_policy', $rules);
        
        // Test with matching context
        $this->assertTrue($this->policyManager->enforcePolicy('admin', 'read', ['resource' => 'public']));
        
        // Test with non-matching context
        $this->assertFalse($this->policyManager->enforcePolicy('admin', 'read', ['resource' => 'private']));
    }

    public function testEnforcePolicyWithMultipleRules(): void
    {
        $rules = [
            [
                'effect' => 'allow',
                'roles' => ['admin'],
                'actions' => ['read']
            ],
            [
                'effect' => 'deny',
                'roles' => ['admin'],
                'actions' => ['write']
            ]
        ];

        $this->policyManager->addPolicy('test_policy', $rules);
        
        $this->assertTrue($this->policyManager->enforcePolicy('admin', 'read'));
        $this->assertFalse($this->policyManager->enforcePolicy('admin', 'write'));
    }

    public function testEnforcePolicyWithDisabledPolicy(): void
    {
        $rules = [
            [
                'effect' => 'deny',
                'roles' => ['admin'],
                'actions' => ['read']
            ]
        ];

        $this->policyManager->addPolicy('test_policy', $rules);
        $this->policyManager->disablePolicy('test_policy');
        
        // Policy should be ignored when disabled
        $this->assertTrue($this->policyManager->enforcePolicy('admin', 'read'));
    }

    public function testEnforcePolicyAuditLogging(): void
    {
        $rules = [
            [
                'effect' => 'allow',
                'roles' => ['admin'],
                'actions' => ['read']
            ]
        ];

        $this->policyManager->addPolicy('test_policy', $rules);
        
        $this->assertTrue($this->policyManager->enforcePolicy('admin', 'read', ['resource' => 'test']));
        
        $log = $this->actionAudit->getAuditLog();
        $this->assertCount(1, $log);
        $this->assertEquals('admin', $log[0]['role']);
        $this->assertEquals('read', $log[0]['action']);
        $this->assertEquals(['resource' => 'test'], $log[0]['details']);
        $this->assertEquals('allowed', $log[0]['result']);
        $this->assertNull($log[0]['error']);
    }
} 