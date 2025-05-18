<?php

namespace App\Mcp\Agent;

interface AgentManagerInterface
{
    public function registerAgent(AgentInterface $agent): bool;
    public function unregisterAgent(string $agentId): bool;
    public function getAgent(string $agentId): ?AgentInterface;
    public function getAgents(): array;
    public function startAgent(string $agentId): bool;
    public function stopAgent(string $agentId): bool;
    public function pauseAgent(string $agentId): bool;
    public function resumeAgent(string $agentId): bool;
    public function sendMessageToAgent(string $agentId, string $message, array $context = []): bool;
    public function broadcastMessage(string $message, array $context = []): void;
    public function getAgentStatus(string $agentId): ?string;
    public function getAgentHealth(string $agentId): ?array;
    public function getAgentPermissions(string $agentId): ?array;
    public function setAgentPermissions(string $agentId, array $permissions): bool;
    public function getAgentMetadata(string $agentId): ?array;
    public function setAgentMetadata(string $agentId, array $metadata): bool;
} 