<?php

namespace LegalStudy\MCP;

interface AgentInterface
{
    /**
     * Initialize the agent
     * @throws \RuntimeException if initialization fails
     */
    public function initialize(): void;

    /**
     * Get the agent's name
     */
    public function getName(): string;

    /**
     * Get the agent's description
     */
    public function getDescription(): string;

    /**
     * Get the agent's capabilities
     * @return array<string> List of capabilities
     */
    public function getCapabilities(): array;

    /**
     * Execute a task
     * @param string $task The task to execute
     * @param array $parameters Task parameters
     * @return mixed Task result
     * @throws \RuntimeException if task execution fails
     */
    public function execute(string $task, array $parameters = []): mixed;

    /**
     * Get the agent's status
     * @return array<string, mixed> Status information
     */
    public function getStatus(): array;

    /**
     * Shutdown the agent
     */
    public function shutdown(): void;
} 