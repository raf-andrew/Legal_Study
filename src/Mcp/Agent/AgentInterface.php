<?php

namespace Mcp\Agent;

interface AgentInterface
{
    /**
     * Initialize the agent with required configuration
     * @param array $config Configuration parameters
     * @return void
     */
    public function initialize(array $config): void;

    /**
     * Execute the agent's primary task
     * @param array $parameters Task parameters
     * @return array Result of the task execution
     */
    public function execute(array $parameters): array;

    /**
     * Get the agent's current status
     * @return array Status information
     */
    public function getStatus(): array;

    /**
     * Handle any errors that occur during execution
     * @param \Throwable $error The error that occurred
     * @return void
     */
    public function handleError(\Throwable $error): void;

    /**
     * Get the agent's required permissions
     * @return array List of required permissions
     */
    public function getRequiredPermissions(): array;

    /**
     * Check if the agent has the required permissions
     * @return bool True if all required permissions are present
     */
    public function hasRequiredPermissions(): bool;

    /**
     * Get the agent's audit log
     * @return array Audit log entries
     */
    public function getAuditLog(): array;

    /**
     * Add an entry to the agent's audit log
     * @param string $action The action performed
     * @param array $details Additional details
     * @return void
     */
    public function logAuditEntry(string $action, array $details): void;
} 