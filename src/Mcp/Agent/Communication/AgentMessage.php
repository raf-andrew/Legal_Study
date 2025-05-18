<?php

namespace Mcp\Agent\Communication;

use Illuminate\Support\Str;
use JsonSerializable;

class AgentMessage implements JsonSerializable
{
    protected string $senderId;
    protected string $receiverId;
    protected string $type;
    protected array $data;
    protected string $timestamp;

    public function __construct(string $senderId, string $receiverId, string $type, array $data = [])
    {
        $this->senderId = $senderId;
        $this->receiverId = $receiverId;
        $this->type = $type;
        $this->data = $data;
        $this->timestamp = now()->toIso8601String();
    }

    public function getSenderId(): string
    {
        return $this->senderId;
    }

    public function getReceiverId(): string
    {
        return $this->receiverId;
    }

    public function getType(): string
    {
        return $this->type;
    }

    public function getData(): array
    {
        return $this->data;
    }

    public function getTimestamp(): string
    {
        return $this->timestamp;
    }

    public function toArray(): array
    {
        return [
            'sender_id' => $this->senderId,
            'receiver_id' => $this->receiverId,
            'type' => $this->type,
            'data' => $this->data,
            'timestamp' => $this->timestamp
        ];
    }

    public function jsonSerialize(): array
    {
        return $this->toArray();
    }
} 