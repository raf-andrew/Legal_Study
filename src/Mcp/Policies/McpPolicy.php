<?php

namespace Mcp\Policies;

use Illuminate\Foundation\Auth\User;
use Illuminate\Support\Facades\Config;

class McpPolicy
{
    /**
     * Determine if the user can access MCP.
     *
     * @param User $user
     * @return bool
     */
    public function access(User $user): bool
    {
        // Check if user has required role
        if (Config::has('mcp.security.authorization.roles')) {
            $requiredRoles = Config::get('mcp.security.authorization.roles', []);
            if (!empty($requiredRoles) && !$user->hasAnyRole($requiredRoles)) {
                return false;
            }
        }

        // Check if user has required permission
        if (Config::has('mcp.security.authorization.permissions')) {
            $requiredPermissions = Config::get('mcp.security.authorization.permissions', []);
            if (!empty($requiredPermissions) && !$user->hasAnyPermission($requiredPermissions)) {
                return false;
            }
        }

        return true;
    }

    /**
     * Determine if the user can discover services.
     *
     * @param User $user
     * @return bool
     */
    public function discover(User $user): bool
    {
        return $this->access($user) && $user->can('mcp.discover');
    }

    /**
     * Determine if the user can monitor services.
     *
     * @param User $user
     * @return bool
     */
    public function monitor(User $user): bool
    {
        return $this->access($user) && $user->can('mcp.monitor');
    }

    /**
     * Determine if the user can manage services.
     *
     * @param User $user
     * @return bool
     */
    public function manage(User $user): bool
    {
        return $this->access($user) && $user->can('mcp.manage');
    }

    /**
     * Determine if the user can configure MCP.
     *
     * @param User $user
     * @return bool
     */
    public function configure(User $user): bool
    {
        return $this->access($user) && $user->can('mcp.configure');
    }

    /**
     * Determine if the user can view MCP logs.
     *
     * @param User $user
     * @return bool
     */
    public function viewLogs(User $user): bool
    {
        return $this->access($user) && $user->can('mcp.view_logs');
    }

    /**
     * Determine if the user can manage MCP users.
     *
     * @param User $user
     * @return bool
     */
    public function manageUsers(User $user): bool
    {
        return $this->access($user) && $user->can('mcp.manage_users');
    }

    /**
     * Determine if the user can manage MCP roles.
     *
     * @param User $user
     * @return bool
     */
    public function manageRoles(User $user): bool
    {
        return $this->access($user) && $user->can('mcp.manage_roles');
    }

    /**
     * Determine if the user can manage MCP permissions.
     *
     * @param User $user
     * @return bool
     */
    public function managePermissions(User $user): bool
    {
        return $this->access($user) && $user->can('mcp.manage_permissions');
    }

    /**
     * Determine if the user can manage MCP settings.
     *
     * @param User $user
     * @return bool
     */
    public function manageSettings(User $user): bool
    {
        return $this->access($user) && $user->can('mcp.manage_settings');
    }
} 