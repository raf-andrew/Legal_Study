<?php

namespace Mcp\Agent;

use Psr\SimpleCache\CacheInterface;
use Psr\Log\LoggerInterface;
use Psr\Log\NullLogger;
use Ramsey\Uuid\Uuid;

class Agent
{
    protected string $id;
    protected string $name;
    protected string $type;
    protected array $capabilities;
    protected array $state;
    protected bool $active;
    protected CacheInterface $cache;
    protected LoggerInterface $logger;

    public function __construct(
        string $name,
        string $type,
        array $capabilities = [],
        ?CacheInterface $cache = null,
        ?LoggerInterface $logger = null
    ) {
        $this->id = Uuid::uuid4()->toString();
        $this->name = $name;
        $this->type = $type;
        $this->capabilities = $capabilities;
        $this->state = [
            'status' => 'initialized',
            'last_active' => time(),
            'tasks_completed' => 0,
            'errors' => 0,
            'memory_usage' => 0,
            'cpu_usage' => 0
        ];
        $this->active = true;
        $this->cache = $cache ?? new class implements CacheInterface {
            public function get($key, $default = null) { return $default; }
            public function set($key, $value, $ttl = null) { return true; }
            public function delete($key) { return true; }
            public function clear() { return true; }
            public function getMultiple($keys, $default = null) { return array_fill_keys($keys, $default); }
            public function setMultiple($values, $ttl = null) { return true; }
            public function deleteMultiple($keys) { return true; }
            public function has($key) { return false; }
        };
        $this->logger = $logger ?? new NullLogger();
    }

    public function getId(): string
    {
        return $this->id;
    }

    public function getName(): string
    {
        return $this->name;
    }

    public function getType(): string
    {
        return $this->type;
    }

    public function getCapabilities(): array
    {
        return $this->capabilities;
    }

    public function hasCapability(string $capability): bool
    {
        return in_array($capability, $this->capabilities);
    }

    public function getState(): array
    {
        return $this->state;
    }

    public function isActive(): bool
    {
        return $this->active;
    }

    public function activate(): void
    {
        $this->active = true;
        $this->updateState('status', 'active');
        $this->logger->info("Agent {$this->name} activated");
    }

    public function deactivate(): void
    {
        $this->active = false;
        $this->updateState('status', 'inactive');
        $this->logger->info("Agent {$this->name} deactivated");
    }

    public function updateState(string $key, $value): void
    {
        $this->state[$key] = $value;
        $this->state['last_active'] = time();
        $this->persistState();
    }

    public function incrementTasksCompleted(): void
    {
        $this->state['tasks_completed']++;
        $this->persistState();
    }

    public function recordError(): void
    {
        $this->state['errors']++;
        $this->persistState();
    }

    public function updateResourceUsage(float $memoryUsage, float $cpuUsage): void
    {
        $this->state['memory_usage'] = $memoryUsage;
        $this->state['cpu_usage'] = $cpuUsage;
        $this->persistState();
    }

    protected function persistState(): void
    {
        $this->cache->set("mcp.agent.{$this->id}.state", $this->state, 3600); // 1 hour TTL
    }

    public function toArray(): array
    {
        return [
            'id' => $this->id,
            'name' => $this->name,
            'type' => $this->type,
            'capabilities' => $this->capabilities,
            'state' => $this->state,
            'active' => $this->active
        ];
    }
}
