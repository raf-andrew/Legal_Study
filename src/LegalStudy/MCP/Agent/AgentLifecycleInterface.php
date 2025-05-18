<?php

namespace LegalStudy\MCP\Agent;

interface AgentLifecycleInterface
{
    public const STATE_INITIALIZED = 'initialized';
    public const STATE_STARTED = 'started';
    public const STATE_STOPPED = 'stopped';
    public const STATE_PAUSED = 'paused';
    public const STATE_ERROR = 'error';

    /**
     * Initialize the agent
     * @throws \RuntimeException if initialization fails
     */
    public function initialize(): void;

    /**
     * Start the agent
     * @throws \RuntimeException if start fails
     */
    public function start(): void;

    /**
     * Stop the agent
     * @throws \RuntimeException if stop fails
     */
    public function stop(): void;

    /**
     * Pause the agent
     * @throws \RuntimeException if pause fails
     */
    public function pause(): void;

    /**
     * Resume the agent
     * @throws \RuntimeException if resume fails
     */
    public function resume(): void;

    /**
     * Restart the agent
     * @throws \RuntimeException if restart fails
     */
    public function restart(): void;

    /**
     * Get the current state of the agent
     * @return string One of: 'initialized', 'started', 'stopped', 'paused', 'error'
     */
    public function getState(): string;

    /**
     * Check if the agent is healthy
     * @return bool True if the agent is healthy, false otherwise
     */
    public function isHealthy(): bool;

    /**
     * Get the last error message if any
     * @return string|null The last error message or null if no error
     */
    public function getLastError(): ?string;

    /**
     * Get the agent's uptime in seconds
     * @return int The uptime in seconds
     */
    public function getUptime(): int;

    /**
     * Get the agent's statistics
     * @return array<string, mixed> The agent's statistics
     */
    public function getStatistics(): array;
} 