<?php

namespace Mcp\Security\Rbac;

class RoleManager
{
    private array $roles;
    private array $permissionRegistry;

    public function __construct()
    {
        $this->roles = [];
        $this->permissionRegistry = [];
    }

    public function createRole(string $name): Role
    {
        if (isset($this->roles[$name])) {
            throw new \InvalidArgumentException("Role '{$name}' already exists");
        }

        $role = new Role($name);
        $this->roles[$name] = $role;
        return $role;
    }

    public function getRole(string $name): ?Role
    {
        return $this->roles[$name] ?? null;
    }

    public function deleteRole(string $name): void
    {
        if (!isset($this->roles[$name])) {
            throw new \InvalidArgumentException("Role '{$name}' does not exist");
        }

        unset($this->roles[$name]);
    }

    public function registerPermission(string $permission, string $description): void
    {
        $this->permissionRegistry[$permission] = $description;
    }

    public function getRegisteredPermissions(): array
    {
        return $this->permissionRegistry;
    }

    public function assignPermission(string $roleName, string $permission): void
    {
        $role = $this->getRole($roleName);
        if (!$role) {
            throw new \InvalidArgumentException("Role '{$roleName}' does not exist");
        }

        if (!isset($this->permissionRegistry[$permission])) {
            throw new \InvalidArgumentException("Permission '{$permission}' is not registered");
        }

        $role->addPermission($permission);
    }

    public function revokePermission(string $roleName, string $permission): void
    {
        $role = $this->getRole($roleName);
        if (!$role) {
            throw new \InvalidArgumentException("Role '{$roleName}' does not exist");
        }

        $role->removePermission($permission);
    }

    public function hasPermission(string $roleName, string $permission): bool
    {
        $role = $this->getRole($roleName);
        if (!$role) {
            return false;
        }

        return $role->hasPermission($permission);
    }

    public function getAllRoles(): array
    {
        return $this->roles;
    }
} 