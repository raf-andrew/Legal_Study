<?php

namespace Mcp\Agent;

use Psr\SimpleCache\CacheInterface;
use Psr\Log\LoggerInterface;
use Psr\Log\NullLogger;
use Mcp\Events\AgentLifecycleEvent;
use Mcp\Events\AgentStateChanged;
use Mcp\Events\AgentErrorOccurred;
use Mcp\Events\AgentResourceUsageUpdated;

class AgentLifecycleManager
{
    protected AgentManager $agentManager;
    protected string $cacheKey = 'mcp.agent.lifecycle';
    protected int $cacheTTL = 3600; // 1 hour
    protected array $lifecycleStates = [];
    protected CacheInterface $cache;
    protected LoggerInterface $logger;

    public function __construct(
        AgentManager $agentManager,
        CacheInterface $cache,
        ?LoggerInterface $logger = null
    ) {
        $this->agentManager = $agentManager;
        $this->cache = $cache;
        $this->logger = $logger ?? new NullLogger();
        $this->lifecycleStates = $this->cache->get($this->cacheKey, []);
    }

    public function initialize(Agent $agent): void
    {
        if (isset($this->lifecycleStates[$agent->getId()])) {
            throw new \InvalidArgumentException("Agent {$agent->getId()} is already initialized");
        }

        $this->lifecycleStates[$agent->getId()] = [
            'status' => 'initialized',
            'initialized_at' => time(),
            'last_heartbeat' => time(),
            'error_count' => 0,
            'resource_usage' => [
                'memory' => 0,
                'cpu' => 0
            ],
            'dependencies' => [],
            'health_status' => 'healthy'
        ];

        $this->persistLifecycleStates();

        $this->logger->info("Agent {$agent->getName()} initialized (event: AgentLifecycleEvent, state: initialized)");
    }

    public function activate(Agent $agent): void
    {
        if (!isset($this->lifecycleStates[$agent->getId()])) {
            throw new \InvalidArgumentException("Agent {$agent->getId()} must be initialized first");
        }

        $state = $this->lifecycleStates[$agent->getId()];
        $state['status'] = 'active';
        $state['activated_at'] = time();
        $this->lifecycleStates[$agent->getId()] = $state;

        $this->persistLifecycleStates();

        $this->logger->info("Agent {$agent->getName()} activated (event: AgentStateChanged, state: active)");
    }

    public function deactivate(Agent $agent): void
    {
        if (!isset($this->lifecycleStates[$agent->getId()])) {
            throw new \InvalidArgumentException("Agent {$agent->getId()} not found");
        }

        $state = $this->lifecycleStates[$agent->getId()];
        $state['status'] = 'inactive';
        $state['deactivated_at'] = time();
        $this->lifecycleStates[$agent->getId()] = $state;

        $this->persistLifecycleStates();

        $this->logger->info("Agent {$agent->getName()} deactivated (event: AgentStateChanged, state: inactive)");
    }

    public function cleanup(Agent $agent): void
    {
        if (!isset($this->lifecycleStates[$agent->getId()])) {
            throw new \InvalidArgumentException("Agent {$agent->getId()} not found");
        }

        unset($this->lifecycleStates[$agent->getId()]);
        $this->persistLifecycleStates();

        $this->logger->info("Agent {$agent->getName()} cleaned up (event: AgentLifecycleEvent, state: cleaned_up)");
    }

    public function recordError(Agent $agent, \Throwable $error): void
    {
        if (!isset($this->lifecycleStates[$agent->getId()])) {
            throw new \InvalidArgumentException("Agent {$agent->getId()} not found");
        }

        $state = $this->lifecycleStates[$agent->getId()];
        $state['error_count']++;
        $state['last_error'] = [
            'message' => $error->getMessage(),
            'code' => $error->getCode(),
            'file' => $error->getFile(),
            'line' => $error->getLine(),
            'trace' => $error->getTraceAsString()
        ];
        $this->lifecycleStates[$agent->getId()] = $state;

        $this->persistLifecycleStates();

        $this->logger->error("Agent {$agent->getName()} error: {$error->getMessage()} (event: AgentErrorOccurred)");
    }

    public function updateResourceUsage(Agent $agent, float $memoryUsage, float $cpuUsage): void
    {
        if (!isset($this->lifecycleStates[$agent->getId()])) {
            throw new \InvalidArgumentException("Agent {$agent->getId()} not found");
        }

        $state = $this->lifecycleStates[$agent->getId()];
        $state['resource_usage'] = [
            'memory' => $memoryUsage,
            'cpu' => $cpuUsage,
            'updated_at' => time()
        ];
        $this->lifecycleStates[$agent->getId()] = $state;

        $this->persistLifecycleStates();

        $this->logger->info("Agent {$agent->getName()} resource usage updated (event: AgentResourceUsageUpdated, memory: $memoryUsage, cpu: $cpuUsage)");
    }

    public function updateHealthStatus(Agent $agent, string $status): void
    {
        if (!isset($this->lifecycleStates[$agent->getId()])) {
            throw new \InvalidArgumentException("Agent {$agent->getId()} not found");
        }

        $state = $this->lifecycleStates[$agent->getId()];
        $state['health_status'] = $status;
        $this->lifecycleStates[$agent->getId()] = $state;

        $this->persistLifecycleStates();

        $this->logger->info("Agent {$agent->getName()} health status updated to {$status}");
    }

    public function updateHeartbeat(Agent $agent): void
    {
        if (!isset($this->lifecycleStates[$agent->getId()])) {
            throw new \InvalidArgumentException("Agent {$agent->getId()} not found");
        }

        $state = $this->lifecycleStates[$agent->getId()];
        $state['last_heartbeat'] = time();
        $this->lifecycleStates[$agent->getId()] = $state;

        $this->persistLifecycleStates();

        $this->logger->debug("Agent {$agent->getName()} heartbeat updated");
    }

    public function getLifecycleState(string $agentId): ?array
    {
        return $this->lifecycleStates[$agentId] ?? null;
    }

    public function getAllLifecycleStates(): array
    {
        return $this->lifecycleStates;
    }

    protected function persistLifecycleStates(): void
    {
        $this->cache->set($this->cacheKey, $this->lifecycleStates, $this->cacheTTL);
    }
}
