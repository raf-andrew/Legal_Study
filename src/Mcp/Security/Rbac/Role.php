<?php

namespace Mcp\Security\Rbac;

class Role
{
    private string $name;
    private array $permissions;
    private array $inheritedRoles;

    public function __construct(string $name)
    {
        $this->name = $name;
        $this->permissions = [];
        $this->inheritedRoles = [];
    }

    public function getName(): string
    {
        return $this->name;
    }

    public function addPermission(string $permission): void
    {
        if (!in_array($permission, $this->permissions)) {
            $this->permissions[] = $permission;
        }
    }

    public function removePermission(string $permission): void
    {
        $this->permissions = array_diff($this->permissions, [$permission]);
    }

    public function hasPermission(string $permission): bool
    {
        return in_array($permission, $this->permissions);
    }

    public function getPermissions(): array
    {
        return $this->permissions;
    }

    public function inheritRole(Role $role): void
    {
        if (!in_array($role->getName(), $this->inheritedRoles)) {
            $this->inheritedRoles[] = $role->getName();
            $this->permissions = array_merge($this->permissions, $role->getPermissions());
        }
    }

    public function getInheritedRoles(): array
    {
        return $this->inheritedRoles;
    }
} 