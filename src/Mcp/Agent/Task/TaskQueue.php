<?php

namespace Mcp\Agent\Task;

use Illuminate\Support\Collection;
use Illuminate\Support\Facades\Cache;
use Illuminate\Support\Facades\Log;
use Illuminate\Support\Facades\Event;

class TaskQueue
{
    protected string $cacheKey = 'mcp.task_queue';
    protected int $cacheTTL = 3600; // 1 hour
    protected Collection $tasks;

    public function __construct()
    {
        $this->tasks = collect(Cache::get($this->cacheKey, []));
    }

    public function enqueue(Task $task): void
    {
        $this->tasks->put($task->getId(), $task);
        $this->persistTasks();
        
        Event::dispatch('mcp.task.queued', [$task]);
        Log::info("Task {$task->getId()} of type {$task->getType()} queued");
    }

    public function dequeue(string $taskId): ?Task
    {
        $task = $this->tasks->pull($taskId);
        
        if ($task !== null) {
            $this->persistTasks();
            Log::info("Task {$taskId} dequeued");
        }
        
        return $task;
    }

    public function getNext(?string $agentId = null, ?array $taskTypes = null): ?Task
    {
        return $this->tasks
            ->filter(function (Task $task) use ($agentId, $taskTypes) {
                if ($task->getStatus() !== Task::STATUS_PENDING) {
                    return false;
                }

                if ($taskTypes !== null && !in_array($task->getType(), $taskTypes)) {
                    return false;
                }

                if ($agentId !== null && $task->getAssignedAgentId() !== null && $task->getAssignedAgentId() !== $agentId) {
                    return false;
                }

                return true;
            })
            ->sortByDesc('priority')
            ->first();
    }

    public function get(string $taskId): ?Task
    {
        return $this->tasks->get($taskId);
    }

    public function getAll(): Collection
    {
        return $this->tasks;
    }

    public function getByStatus(string $status): Collection
    {
        return $this->tasks->filter(function (Task $task) use ($status) {
            return $task->getStatus() === $status;
        });
    }

    public function getByAgent(string $agentId): Collection
    {
        return $this->tasks->filter(function (Task $task) use ($agentId) {
            return $task->getAssignedAgentId() === $agentId;
        });
    }

    public function getByType(string $type): Collection
    {
        return $this->tasks->filter(function (Task $task) use ($type) {
            return $task->getType() === $type;
        });
    }

    public function update(Task $task): void
    {
        if (!$this->tasks->has($task->getId())) {
            throw new \InvalidArgumentException("Task {$task->getId()} not found in queue");
        }

        $this->tasks->put($task->getId(), $task);
        $this->persistTasks();
        
        Event::dispatch('mcp.task.updated', [$task]);
        Log::info("Task {$task->getId()} updated with status {$task->getStatus()}");
    }

    public function clear(): void
    {
        $this->tasks = collect();
        Cache::forget($this->cacheKey);
        Log::info('Task queue cleared');
    }

    public function checkTimeouts(): void
    {
        $timeoutCount = 0;
        
        $this->tasks->each(function (Task $task) use (&$timeoutCount) {
            if ($task->getStatus() === Task::STATUS_RUNNING) {
                $task->timeout();
                if ($task->getStatus() === Task::STATUS_TIMEOUT) {
                    $timeoutCount++;
                    Event::dispatch('mcp.task.timeout', [$task]);
                }
            }
        });
        
        if ($timeoutCount > 0) {
            $this->persistTasks();
            Log::info("Detected {$timeoutCount} timed out tasks");
        }
    }

    public function getQueueStats(): array
    {
        return [
            'total_tasks' => $this->tasks->count(),
            'pending_tasks' => $this->getByStatus(Task::STATUS_PENDING)->count(),
            'running_tasks' => $this->getByStatus(Task::STATUS_RUNNING)->count(),
            'completed_tasks' => $this->getByStatus(Task::STATUS_COMPLETED)->count(),
            'failed_tasks' => $this->getByStatus(Task::STATUS_FAILED)->count(),
            'timeout_tasks' => $this->getByStatus(Task::STATUS_TIMEOUT)->count(),
            'average_completion_time' => $this->calculateAverageCompletionTime(),
            'success_rate' => $this->calculateSuccessRate()
        ];
    }

    protected function calculateAverageCompletionTime(): float
    {
        $completedTasks = $this->getByStatus(Task::STATUS_COMPLETED);
        
        if ($completedTasks->isEmpty()) {
            return 0.0;
        }

        $totalTime = $completedTasks->sum(function (Task $task) {
            return $task->getCompletedAt() - $task->getStartedAt();
        });

        return $totalTime / $completedTasks->count();
    }

    protected function calculateSuccessRate(): float
    {
        $totalTasks = $this->tasks->filter(function (Task $task) {
            return in_array($task->getStatus(), [
                Task::STATUS_COMPLETED,
                Task::STATUS_FAILED,
                Task::STATUS_TIMEOUT
            ]);
        })->count();

        if ($totalTasks === 0) {
            return 0.0;
        }

        $completedTasks = $this->getByStatus(Task::STATUS_COMPLETED)->count();
        return ($completedTasks / $totalTasks) * 100;
    }

    protected function persistTasks(): void
    {
        Cache::put(
            $this->cacheKey,
            $this->tasks->all(),
            now()->addSeconds($this->cacheTTL)
        );
    }
} 