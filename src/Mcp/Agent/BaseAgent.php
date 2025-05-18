<?php

namespace App\Mcp\Agent;

use Illuminate\Support\Facades\Log;

abstract class BaseAgent implements AgentInterface
{
    protected $id;
    protected $capabilities = [];
    protected $state = [];
    protected $metadata = [];

    public function __construct(string $id, array $capabilities = [], array $metadata = [])
    {
        $this->id = $id;
        $this->capabilities = $capabilities;
        $this->metadata = $metadata;
        $this->initialize();
    }

    protected function initialize()
    {
        // Override in child classes to perform initialization
    }

    public function getId(): string
    {
        return $this->id;
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

    public function setState(array $state): void
    {
        $this->state = $state;
    }

    public function getMetadata(): array
    {
        return $this->metadata;
    }

    public function handleEvent(string $event, array $data = []): void
    {
        $method = 'handle' . str_replace(' ', '', ucwords(str_replace('.', ' ', $event)));
        
        if (method_exists($this, $method)) {
            $this->$method($data);
        } else {
            Log::debug("MCP Agent {$this->id}: No handler for event {$event}");
        }
    }

    protected function log(string $message, string $level = 'info'): void
    {
        Log::{$level}("MCP Agent {$this->id}: {$message}");
    }

    protected function updateState(array $updates): void
    {
        $this->state = array_merge($this->state, $updates);
    }

    protected function addCapability(string $capability): void
    {
        if (!in_array($capability, $this->capabilities)) {
            $this->capabilities[] = $capability;
        }
    }

    protected function removeCapability(string $capability): void
    {
        $this->capabilities = array_diff($this->capabilities, [$capability]);
    }

    protected function updateMetadata(array $updates): void
    {
        $this->metadata = array_merge($this->metadata, $updates);
    }
} 