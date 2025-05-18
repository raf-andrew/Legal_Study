<?php

namespace Tests\Mcp\Security\Rbac;

use Mcp\Security\Rbac\RoleManager;
use PHPUnit\Framework\TestCase;

class RoleManagerTest extends TestCase
{
    private RoleManager $roleManager;

    protected function setUp(): void
    {
        $this->roleManager = new RoleManager();
    }

    public function testCreateRole(): void
    {
        $role = $this->roleManager->createRole('test_role');
        $this->assertEquals('test_role', $role->getName());
    }

    public function testCreateDuplicateRole(): void
    {
        $this->roleManager->createRole('test_role');
        $this->expectException(\InvalidArgumentException::class);
        $this->roleManager->createRole('test_role');
    }

    public function testGetRole(): void
    {
        $this->roleManager->createRole('test_role');
        $role = $this->roleManager->getRole('test_role');
        $this->assertNotNull($role);
        $this->assertEquals('test_role', $role->getName());
    }

    public function testGetNonExistentRole(): void
    {
        $role = $this->roleManager->getRole('non_existent');
        $this->assertNull($role);
    }

    public function testDeleteRole(): void
    {
        $this->roleManager->createRole('test_role');
        $this->roleManager->deleteRole('test_role');
        $this->assertNull($this->roleManager->getRole('test_role'));
    }

    public function testDeleteNonExistentRole(): void
    {
        $this->expectException(\InvalidArgumentException::class);
        $this->roleManager->deleteRole('non_existent');
    }

    public function testRegisterPermission(): void
    {
        $this->roleManager->registerPermission('test.permission', 'Test permission');
        $permissions = $this->roleManager->getRegisteredPermissions();
        $this->assertArrayHasKey('test.permission', $permissions);
        $this->assertEquals('Test permission', $permissions['test.permission']);
    }

    public function testAssignPermission(): void
    {
        $this->roleManager->createRole('test_role');
        $this->roleManager->registerPermission('test.permission', 'Test permission');
        $this->roleManager->assignPermission('test_role', 'test.permission');
        
        $role = $this->roleManager->getRole('test_role');
        $this->assertTrue($role->hasPermission('test.permission'));
    }

    public function testAssignUnregisteredPermission(): void
    {
        $this->roleManager->createRole('test_role');
        $this->expectException(\InvalidArgumentException::class);
        $this->roleManager->assignPermission('test_role', 'unregistered.permission');
    }

    public function testRevokePermission(): void
    {
        $this->roleManager->createRole('test_role');
        $this->roleManager->registerPermission('test.permission', 'Test permission');
        $this->roleManager->assignPermission('test_role', 'test.permission');
        $this->roleManager->revokePermission('test_role', 'test.permission');
        
        $role = $this->roleManager->getRole('test_role');
        $this->assertFalse($role->hasPermission('test.permission'));
    }

    public function testHasPermission(): void
    {
        $this->roleManager->createRole('test_role');
        $this->roleManager->registerPermission('test.permission', 'Test permission');
        $this->roleManager->assignPermission('test_role', 'test.permission');
        
        $this->assertTrue($this->roleManager->hasPermission('test_role', 'test.permission'));
        $this->assertFalse($this->roleManager->hasPermission('test_role', 'other.permission'));
    }

    public function testGetAllRoles(): void
    {
        $this->roleManager->createRole('role1');
        $this->roleManager->createRole('role2');
        
        $roles = $this->roleManager->getAllRoles();
        $this->assertCount(2, $roles);
        $this->assertArrayHasKey('role1', $roles);
        $this->assertArrayHasKey('role2', $roles);
    }
} 