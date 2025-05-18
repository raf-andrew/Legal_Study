<?php

namespace App\Mcp\Agent;

interface AgentInterface
{
    public function getId(): string;
    public function getName(): string;
    public function getStatus(): string;
    public function start(): bool;
    public function stop(): bool;
    public function pause(): bool;
    public function resume(): bool;
    public function sendMessage(string $message, array $context = []): bool;
    public function receiveMessage(string $message, array $context = []): bool;
    public function getPermissions(): array;
    public function setPermissions(array $permissions): bool;
    public function getMetadata(): array;
    public function setMetadata(array $metadata): bool;
    public function getHealth(): array;
    public function log(string $message, string $level = 'info'): void;
} 