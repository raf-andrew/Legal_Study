<?php

namespace Mcp\Security\Rbac;

class SecurityPolicyManager
{
    private array $policies;
    private RoleManager $roleManager;
    private ActionAudit $actionAudit;

    public function __construct(RoleManager $roleManager, ActionAudit $actionAudit)
    {
        $this->policies = [];
        $this->roleManager = $roleManager;
        $this->actionAudit = $actionAudit;
    }

    public function addPolicy(string $name, array $rules): void
    {
        $this->policies[$name] = [
            'rules' => $rules,
            'enabled' => true
        ];
    }

    public function removePolicy(string $name): void
    {
        unset($this->policies[$name]);
    }

    public function enablePolicy(string $name): void
    {
        if (!isset($this->policies[$name])) {
            throw new \InvalidArgumentException("Policy '{$name}' does not exist");
        }
        $this->policies[$name]['enabled'] = true;
    }

    public function disablePolicy(string $name): void
    {
        if (!isset($this->policies[$name])) {
            throw new \InvalidArgumentException("Policy '{$name}' does not exist");
        }
        $this->policies[$name]['enabled'] = false;
    }

    public function isPolicyEnabled(string $name): bool
    {
        return $this->policies[$name]['enabled'] ?? false;
    }

    public function enforcePolicy(string $roleName, string $action, array $context = []): bool
    {
        $hasEnabledPolicies = false;
        $policyViolations = [];
        $allowed = false;

        foreach ($this->policies as $name => $policy) {
            if (!$policy['enabled']) {
                continue;
            }

            $hasEnabledPolicies = true;
            $matchedRule = false;

            foreach ($policy['rules'] as $rule) {
                // Check if the rule applies to this request
                if (isset($rule['roles']) && !in_array($roleName, $rule['roles'])) {
                    continue;
                }

                if (isset($rule['actions']) && !in_array($action, $rule['actions'])) {
                    continue;
                }

                if (isset($rule['conditions'])) {
                    $conditionsMatch = true;
                    foreach ($rule['conditions'] as $key => $value) {
                        if (!isset($context[$key]) || $context[$key] !== $value) {
                            $conditionsMatch = false;
                            break;
                        }
                    }
                    if (!$conditionsMatch) {
                        continue;
                    }
                }

                // Rule matches, apply its effect
                $matchedRule = true;
                if ($rule['effect'] === 'allow') {
                    $allowed = true;
                } else {
                    $allowed = false;
                    $policyViolations[] = $name;
                }
                break;
            }

            // If no rules matched in this policy, deny access
            if (!$matchedRule) {
                $allowed = false;
                $policyViolations[] = $name;
            }
        }

        // If no enabled policies, allow access
        if (!$hasEnabledPolicies) {
            $allowed = true;
        }

        $this->actionAudit->logAction(
            $roleName,
            $action,
            $context,
            $allowed ? 'allowed' : 'denied',
            $allowed ? null : 'Policy violations: ' . implode(', ', $policyViolations)
        );

        return $allowed;
    }

    public function getPolicies(): array
    {
        return $this->policies;
    }
} 