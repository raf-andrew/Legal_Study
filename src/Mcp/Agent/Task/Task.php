<?php

namespace Mcp\Agent\Task;

use Illuminate\Support\Str;
use JsonSerializable;

class Task implements JsonSerializable
{
    protected string $id;
    protected string $type;
    protected array $parameters;
    protected string $status;
    protected ?string $assignedAgentId;
    protected int $priority;
    protected int $createdAt;
    protected ?int $startedAt;
    protected ?int $completedAt;
    protected array $result;
    protected array $errors;
    protected int $attempts;
    protected int $maxAttempts;
    protected int $timeout;

    public const STATUS_PENDING = 'pending';
    public const STATUS_ASSIGNED = 'assigned';
    public const STATUS_RUNNING = 'running';
    public const STATUS_COMPLETED = 'completed';
    public const STATUS_FAILED = 'failed';
    public const STATUS_TIMEOUT = 'timeout';

    public function __construct(
        string $type,
        array $parameters = [],
        int $priority = 0,
        int $maxAttempts = 3,
        int $timeout = 3600
    ) {
        $this->id = Str::uuid();
        $this->type = $type;
        $this->parameters = $parameters;
        $this->status = self::STATUS_PENDING;
        $this->assignedAgentId = null;
        $this->priority = $priority;
        $this->createdAt = time();
        $this->startedAt = null;
        $this->completedAt = null;
        $this->result = [];
        $this->errors = [];
        $this->attempts = 0;
        $this->maxAttempts = $maxAttempts;
        $this->timeout = $timeout;
    }

    public function getId(): string
    {
        return $this->id;
    }

    public function getType(): string
    {
        return $this->type;
    }

    public function getParameters(): array
    {
        return $this->parameters;
    }

    public function getStatus(): string
    {
        return $this->status;
    }

    public function getAssignedAgentId(): ?string
    {
        return $this->assignedAgentId;
    }

    public function getPriority(): int
    {
        return $this->priority;
    }

    public function getCreatedAt(): int
    {
        return $this->createdAt;
    }

    public function getStartedAt(): ?int
    {
        return $this->startedAt;
    }

    public function getCompletedAt(): ?int
    {
        return $this->completedAt;
    }

    public function getResult(): array
    {
        return $this->result;
    }

    public function getErrors(): array
    {
        return $this->errors;
    }

    public function getAttempts(): int
    {
        return $this->attempts;
    }

    public function getMaxAttempts(): int
    {
        return $this->maxAttempts;
    }

    public function getTimeout(): int
    {
        return $this->timeout;
    }

    public function assign(string $agentId): void
    {
        $this->assignedAgentId = $agentId;
        $this->status = self::STATUS_ASSIGNED;
    }

    public function start(): void
    {
        if ($this->status !== self::STATUS_ASSIGNED) {
            throw new \RuntimeException('Task must be assigned before starting');
        }

        $this->attempts++;
        $this->startedAt = time();
        $this->status = self::STATUS_RUNNING;
    }

    public function complete(array $result = []): void
    {
        if ($this->status !== self::STATUS_RUNNING) {
            throw new \RuntimeException('Task must be running before completing');
        }

        $this->completedAt = time();
        $this->result = $result;
        $this->status = self::STATUS_COMPLETED;
    }

    public function fail(string $error): void
    {
        $this->errors[] = [
            'message' => $error,
            'timestamp' => time(),
            'attempt' => $this->attempts
        ];

        if ($this->attempts >= $this->maxAttempts) {
            $this->status = self::STATUS_FAILED;
        } else {
            $this->status = self::STATUS_PENDING;
            $this->assignedAgentId = null;
            $this->startedAt = null;
        }
    }

    public function timeout(): void
    {
        if ($this->status === self::STATUS_RUNNING && time() > ($this->startedAt + $this->timeout)) {
            $this->errors[] = [
                'message' => 'Task timed out',
                'timestamp' => time(),
                'attempt' => $this->attempts
            ];
            
            $this->status = self::STATUS_TIMEOUT;
        }
    }

    public function canRetry(): bool
    {
        return $this->attempts < $this->maxAttempts &&
            ($this->status === self::STATUS_PENDING ||
             $this->status === self::STATUS_TIMEOUT);
    }

    public function jsonSerialize(): array
    {
        return [
            'id' => $this->id,
            'type' => $this->type,
            'parameters' => $this->parameters,
            'status' => $this->status,
            'assigned_agent_id' => $this->assignedAgentId,
            'priority' => $this->priority,
            'created_at' => $this->createdAt,
            'started_at' => $this->startedAt,
            'completed_at' => $this->completedAt,
            'result' => $this->result,
            'errors' => $this->errors,
            'attempts' => $this->attempts,
            'max_attempts' => $this->maxAttempts,
            'timeout' => $this->timeout
        ];
    }

    public static function fromArray(array $data): self
    {
        $task = new self(
            $data['type'],
            $data['parameters'] ?? [],
            $data['priority'] ?? 0,
            $data['max_attempts'] ?? 3,
            $data['timeout'] ?? 3600
        );

        $task->id = $data['id'];
        $task->status = $data['status'];
        $task->assignedAgentId = $data['assigned_agent_id'];
        $task->createdAt = $data['created_at'];
        $task->startedAt = $data['started_at'];
        $task->completedAt = $data['completed_at'];
        $task->result = $data['result'];
        $task->errors = $data['errors'];
        $task->attempts = $data['attempts'];

        return $task;
    }
} 