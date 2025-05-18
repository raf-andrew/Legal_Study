<?php

namespace Mcp\Agent;

use Psr\SimpleCache\CacheInterface;
use Psr\Log\LoggerInterface;
use Psr\Log\NullLogger;

class AgentManager
{
    protected array $agents = [];
    protected string $cacheKey = 'mcp.agents';
    protected int $cacheTTL = 3600; // 1 hour
    protected CacheInterface $cache;
    protected LoggerInterface $logger;

    public function __construct(
        CacheInterface $cache,
        ?LoggerInterface $logger = null
    ) {
        $this->cache = $cache;
        $this->logger = $logger ?? new NullLogger();
        $this->agents = $this->cache->get($this->cacheKey, []);
    }

    public function register(Agent $agent): void
    {
        if (isset($this->agents[$agent->getId()])) {
            throw new \InvalidArgumentException("Agent with ID {$agent->getId()} already exists");
        }

        $this->agents[$agent->getId()] = $agent;
        $this->persistAgents();

        $this->logger->info("Agent {$agent->getName()} registered with ID {$agent->getId()}");
    }

    public function unregister(string $agentId): void
    {
        if (!isset($this->agents[$agentId])) {
            throw new \InvalidArgumentException("Agent with ID {$agentId} not found");
        }

        $agent = $this->agents[$agentId];
        unset($this->agents[$agentId]);
        $this->persistAgents();

        $this->logger->info("Agent {$agent->getName()} unregistered");
    }

    public function get(string $agentId): ?Agent
    {
        return $this->agents[$agentId] ?? null;
    }

    public function getAll(): array
    {
        return $this->agents;
    }

    public function getByType(string $type): array
    {
        return array_filter($this->agents, function (Agent $agent) use ($type) {
            return $agent->getType() === $type;
        });
    }

    public function getByCapability(string $capability): array
    {
        return array_filter($this->agents, function (Agent $agent) use ($capability) {
            return $agent->hasCapability($capability);
        });
    }

    public function getActive(): array
    {
        return array_filter($this->agents, function (Agent $agent) {
            return $agent->isActive();
        });
    }

    public function activateAll(): void
    {
        foreach ($this->agents as $agent) {
            $agent->activate();
        }
        $this->persistAgents();
    }

    public function deactivateAll(): void
    {
        foreach ($this->agents as $agent) {
            $agent->deactivate();
        }
        $this->persistAgents();
    }

    public function clear(): void
    {
        $this->agents = [];
        $this->cache->delete($this->cacheKey);
        $this->logger->info('All agents cleared');
    }

    protected function persistAgents(): void
    {
        $agentsArray = array_map(function (Agent $agent) {
            return $agent->toArray();
        }, $this->agents);

        $this->cache->set($this->cacheKey, $agentsArray, $this->cacheTTL);
    }

    public function getAgentStates(): array
    {
        return array_map(function (Agent $agent) {
            return [
                'id' => $agent->getId(),
                'name' => $agent->getName(),
                'type' => $agent->getType(),
                'state' => $agent->getState()
            ];
        }, $this->agents);
    }

    public function getSystemMetrics(): array
    {
        $activeAgents = $this->getActive();
        $totalTasksCompleted = array_sum(array_map(function (Agent $agent) {
            return $agent->getState()['tasks_completed'];
        }, $this->agents));
        $totalErrors = array_sum(array_map(function (Agent $agent) {
            return $agent->getState()['errors'];
        }, $this->agents));
        $memoryUsage = array_map(function (Agent $agent) {
            return $agent->getState()['memory_usage'];
        }, $this->agents);
        $cpuUsage = array_map(function (Agent $agent) {
            return $agent->getState()['cpu_usage'];
        }, $this->agents);

        return [
            'total_agents' => count($this->agents),
            'active_agents' => count($activeAgents),
            'total_tasks_completed' => $totalTasksCompleted,
            'total_errors' => $totalErrors,
            'average_memory_usage' => count($memoryUsage) ? array_sum($memoryUsage) / count($memoryUsage) : 0,
            'average_cpu_usage' => count($cpuUsage) ? array_sum($cpuUsage) / count($cpuUsage) : 0
        ];
    }
}
