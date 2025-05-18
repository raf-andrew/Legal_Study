<?php

namespace App\Mcp\Agent;

class AgentManager implements AgentManagerInterface
{
    protected array $agents = [];

    public function registerAgent(AgentInterface $agent): bool
    {
        $id = $agent->getId();
        if (isset($this->agents[$id])) {
            return false;
        }
        $this->agents[$id] = $agent;
        return true;
    }

    public function unregisterAgent(string $agentId): bool
    {
        if (!isset($this->agents[$agentId])) {
            return false;
        }
        unset($this->agents[$agentId]);
        return true;
    }

    public function getAgent(string $agentId): ?AgentInterface
    {
        return $this->agents[$agentId] ?? null;
    }

    public function getAgents(): array
    {
        return $this->agents;
    }

    public function startAgent(string $agentId): bool
    {
        return isset($this->agents[$agentId]) ? $this->agents[$agentId]->start() : false;
    }

    public function stopAgent(string $agentId): bool
    {
        return isset($this->agents[$agentId]) ? $this->agents[$agentId]->stop() : false;
    }

    public function pauseAgent(string $agentId): bool
    {
        return isset($this->agents[$agentId]) ? $this->agents[$agentId]->pause() : false;
    }

    public function resumeAgent(string $agentId): bool
    {
        return isset($this->agents[$agentId]) ? $this->agents[$agentId]->resume() : false;
    }

    public function sendMessageToAgent(string $agentId, string $message, array $context = []): bool
    {
        return isset($this->agents[$agentId]) ? $this->agents[$agentId]->receiveMessage($message, $context) : false;
    }

    public function broadcastMessage(string $message, array $context = []): void
    {
        foreach ($this->agents as $agent) {
            $agent->receiveMessage($message, $context);
        }
    }

    public function getAgentStatus(string $agentId): ?string
    {
        return isset($this->agents[$agentId]) ? $this->agents[$agentId]->getStatus() : null;
    }

    public function getAgentHealth(string $agentId): ?array
    {
        return isset($this->agents[$agentId]) ? $this->agents[$agentId]->getHealth() : null;
    }

    public function getAgentPermissions(string $agentId): ?array
    {
        return isset($this->agents[$agentId]) ? $this->agents[$agentId]->getPermissions() : null;
    }

    public function setAgentPermissions(string $agentId, array $permissions): bool
    {
        return isset($this->agents[$agentId]) ? $this->agents[$agentId]->setPermissions($permissions) : false;
    }

    public function getAgentMetadata(string $agentId): ?array
    {
        return isset($this->agents[$agentId]) ? $this->agents[$agentId]->getMetadata() : null;
    }

    public function setAgentMetadata(string $agentId, array $metadata): bool
    {
        return isset($this->agents[$agentId]) ? $this->agents[$agentId]->setMetadata($metadata) : false;
    }
} 