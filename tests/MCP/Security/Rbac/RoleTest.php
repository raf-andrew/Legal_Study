<?php

namespace Tests\Mcp\Security\Rbac;

use Mcp\Security\Rbac\Role;
use PHPUnit\Framework\TestCase;

class RoleTest extends TestCase
{
    private Role $role;

    protected function setUp(): void
    {
        $this->role = new Role('test_role');
    }

    public function testGetName(): void
    {
        $this->assertEquals('test_role', $this->role->getName());
    }

    public function testAddPermission(): void
    {
        $this->role->addPermission('test.permission');
        $this->assertTrue($this->role->hasPermission('test.permission'));
    }

    public function testRemovePermission(): void
    {
        $this->role->addPermission('test.permission');
        $this->role->removePermission('test.permission');
        $this->assertFalse($this->role->hasPermission('test.permission'));
    }

    public function testGetPermissions(): void
    {
        $this->role->addPermission('test.permission1');
        $this->role->addPermission('test.permission2');
        
        $permissions = $this->role->getPermissions();
        $this->assertCount(2, $permissions);
        $this->assertContains('test.permission1', $permissions);
        $this->assertContains('test.permission2', $permissions);
    }

    public function testInheritRole(): void
    {
        $parentRole = new Role('parent_role');
        $parentRole->addPermission('parent.permission');
        
        $this->role->inheritRole($parentRole);
        
        $this->assertTrue($this->role->hasPermission('parent.permission'));
        $this->assertContains('parent_role', $this->role->getInheritedRoles());
    }

    public function testGetInheritedRoles(): void
    {
        $parentRole1 = new Role('parent1');
        $parentRole2 = new Role('parent2');
        
        $this->role->inheritRole($parentRole1);
        $this->role->inheritRole($parentRole2);
        
        $inheritedRoles = $this->role->getInheritedRoles();
        $this->assertCount(2, $inheritedRoles);
        $this->assertContains('parent1', $inheritedRoles);
        $this->assertContains('parent2', $inheritedRoles);
    }
} 