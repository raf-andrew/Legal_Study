<?php

namespace App\Mcp\Agent;

class Agent implements AgentInterface
{
    protected string $id;
    protected string $name;
    protected string $status = 'created';
    protected array $permissions = [];
    protected array $metadata = [];
    protected array $health = [];

    public function __construct(string $id, string $name, array $metadata = [])
    {
        $this->id = $id;
        $this->name = $name;
        $this->metadata = $metadata;
    }

    public function getId(): string { return $this->id; }
    public function getName(): string { return $this->name; }
    public function getStatus(): string { return $this->status; }
    public function start(): bool { $this->status = 'running'; return true; }
    public function stop(): bool { $this->status = 'stopped'; return true; }
    public function pause(): bool { $this->status = 'paused'; return true; }
    public function resume(): bool { $this->status = 'running'; return true; }
    public function sendMessage(string $message, array $context = []): bool { return true; }
    public function receiveMessage(string $message, array $context = []): bool { return true; }
    public function getPermissions(): array { return $this->permissions; }
    public function setPermissions(array $permissions): bool { $this->permissions = $permissions; return true; }
    public function getMetadata(): array { return $this->metadata; }
    public function setMetadata(array $metadata): bool { $this->metadata = $metadata; return true; }
    public function getHealth(): array { return $this->health; }
    public function log(string $message, string $level = 'info'): void { /* stub */ }
} 