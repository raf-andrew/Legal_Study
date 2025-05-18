<?php

namespace Tests\Mcp\Policies;

use Mcp\Policies\McpPolicy;
use Tests\TestCase;
use Illuminate\Support\Facades\Config;
use Mockery;

class McpPolicyTest extends TestCase
{
    private McpPolicy $policy;

    protected function setUp(): void
    {
        parent::setUp();
        $this->policy = new McpPolicy();
    }

    public function testAccessWithoutRequirements(): void
    {
        Config::set('mcp.security.require_roles', []);
        Config::set('mcp.security.require_permissions', []);

        $user = Mockery::mock('Illuminate\Contracts\Auth\Authenticatable');
        
        $this->assertTrue($this->policy->access($user));
    }

    public function testAccessWithRequiredRole(): void
    {
        Config::set('mcp.security.require_roles', ['admin']);
        Config::set('mcp.security.require_permissions', []);

        $user = Mockery::mock('Illuminate\Contracts\Auth\Authenticatable');
        $user->shouldReceive('hasRole')
            ->once()
            ->with('admin')
            ->andReturn(true);
        
        $this->assertTrue($this->policy->access($user));
    }

    public function testAccessWithRequiredPermission(): void
    {
        Config::set('mcp.security.require_roles', []);
        Config::set('mcp.security.require_permissions', ['mcp.access']);

        $user = Mockery::mock('Illuminate\Contracts\Auth\Authenticatable');
        $user->shouldReceive('hasPermission')
            ->once()
            ->with('mcp.access')
            ->andReturn(true);
        
        $this->assertTrue($this->policy->access($user));
    }

    public function testAccessDeniedWithMissingRole(): void
    {
        Config::set('mcp.security.require_roles', ['admin']);
        Config::set('mcp.security.require_permissions', []);

        $user = Mockery::mock('Illuminate\Contracts\Auth\Authenticatable');
        $user->shouldReceive('hasRole')
            ->once()
            ->with('admin')
            ->andReturn(false);
        
        $this->assertFalse($this->policy->access($user));
    }

    public function testAccessDeniedWithMissingPermission(): void
    {
        Config::set('mcp.security.require_roles', []);
        Config::set('mcp.security.require_permissions', ['mcp.access']);

        $user = Mockery::mock('Illuminate\Contracts\Auth\Authenticatable');
        $user->shouldReceive('hasPermission')
            ->once()
            ->with('mcp.access')
            ->andReturn(false);
        
        $this->assertFalse($this->policy->access($user));
    }

    public function testDiscoverPermission(): void
    {
        $user = Mockery::mock('Illuminate\Contracts\Auth\Authenticatable');
        $user->shouldReceive('hasPermission')
            ->once()
            ->with('mcp.discover')
            ->andReturn(true);
        
        $this->assertTrue($this->policy->discover($user));
    }

    public function testMonitorPermission(): void
    {
        $user = Mockery::mock('Illuminate\Contracts\Auth\Authenticatable');
        $user->shouldReceive('hasPermission')
            ->once()
            ->with('mcp.monitor')
            ->andReturn(true);
        
        $this->assertTrue($this->policy->monitor($user));
    }

    public function testManagePermission(): void
    {
        $user = Mockery::mock('Illuminate\Contracts\Auth\Authenticatable');
        $user->shouldReceive('hasPermission')
            ->once()
            ->with('mcp.manage')
            ->andReturn(true);
        
        $this->assertTrue($this->policy->manage($user));
    }

    public function testConfigurePermission(): void
    {
        $user = Mockery::mock('Illuminate\Contracts\Auth\Authenticatable');
        $user->shouldReceive('hasPermission')
            ->once()
            ->with('mcp.configure')
            ->andReturn(true);
        
        $this->assertTrue($this->policy->configure($user));
    }

    public function testViewLogsPermission(): void
    {
        $user = Mockery::mock('Illuminate\Contracts\Auth\Authenticatable');
        $user->shouldReceive('hasPermission')
            ->once()
            ->with('mcp.view_logs')
            ->andReturn(true);
        
        $this->assertTrue($this->policy->viewLogs($user));
    }

    public function testManageUsersPermission(): void
    {
        $user = Mockery::mock('Illuminate\Contracts\Auth\Authenticatable');
        $user->shouldReceive('hasPermission')
            ->once()
            ->with('mcp.manage_users')
            ->andReturn(true);
        
        $this->assertTrue($this->policy->manageUsers($user));
    }

    public function testManageRolesPermission(): void
    {
        $user = Mockery::mock('Illuminate\Contracts\Auth\Authenticatable');
        $user->shouldReceive('hasPermission')
            ->once()
            ->with('mcp.manage_roles')
            ->andReturn(true);
        
        $this->assertTrue($this->policy->manageRoles($user));
    }

    public function testManagePermissionsPermission(): void
    {
        $user = Mockery::mock('Illuminate\Contracts\Auth\Authenticatable');
        $user->shouldReceive('hasPermission')
            ->once()
            ->with('mcp.manage_permissions')
            ->andReturn(true);
        
        $this->assertTrue($this->policy->managePermissions($user));
    }

    public function testManageSettingsPermission(): void
    {
        $user = Mockery::mock('Illuminate\Contracts\Auth\Authenticatable');
        $user->shouldReceive('hasPermission')
            ->once()
            ->with('mcp.manage_settings')
            ->andReturn(true);
        
        $this->assertTrue($this->policy->manageSettings($user));
    }
} 