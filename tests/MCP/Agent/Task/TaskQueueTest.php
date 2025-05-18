<?php

namespace Tests\Mcp\Agent\Task;

use Mcp\Agent\Task\TaskQueue;
use Mcp\Agent\Task\Task;
use Tests\TestCase;
use Illuminate\Support\Facades\Cache;
use Illuminate\Support\Facades\Log;
use Illuminate\Support\Facades\Event;
use Mockery;

class TaskQueueTest extends TestCase
{
    private TaskQueue $queue;
    private Task $task;
    private string $agentId = 'agent-123';

    protected function setUp(): void
    {
        parent::setUp();
        
        Cache::flush();
        
        $this->queue = new TaskQueue();
        $this->task = new Task('test.task', ['key' => 'value']);
    }

    public function testTaskEnqueue(): void
    {
        Event::fake();
        Log::shouldReceive('info')
            ->once()
            ->with("Task {$this->task->getId()} of type {$this->task->getType()} queued");

        $this->queue->enqueue($this->task);
        
        Event::assertDispatched('mcp.task.queued', function ($eventName, $args) {
            return $args[0] === $this->task;
        });
        
        $this->assertEquals($this->task, $this->queue->get($this->task->getId()));
    }

    public function testTaskDequeue(): void
    {
        $this->queue->enqueue($this->task);

        Log::shouldReceive('info')
            ->once()
            ->with("Task {$this->task->getId()} dequeued");

        $dequeuedTask = $this->queue->dequeue($this->task->getId());
        
        $this->assertEquals($this->task, $dequeuedTask);
        $this->assertNull($this->queue->get($this->task->getId()));
    }

    public function testGetNextTask(): void
    {
        $task1 = new Task('test.task', [], 1); // priority 1
        $task2 = new Task('test.task', [], 2); // priority 2
        
        $this->queue->enqueue($task1);
        $this->queue->enqueue($task2);
        
        $nextTask = $this->queue->getNext();
        
        $this->assertEquals($task2, $nextTask); // Higher priority task should be returned
    }

    public function testGetNextTaskWithType(): void
    {
        $task1 = new Task('test.task1', []);
        $task2 = new Task('test.task2', []);
        
        $this->queue->enqueue($task1);
        $this->queue->enqueue($task2);
        
        $nextTask = $this->queue->getNext(null, ['test.task2']);
        
        $this->assertEquals($task2, $nextTask);
    }

    public function testGetNextTaskWithAgent(): void
    {
        $task1 = new Task('test.task', []);
        $task2 = new Task('test.task', []);
        
        $task1->assign($this->agentId);
        
        $this->queue->enqueue($task1);
        $this->queue->enqueue($task2);
        
        $nextTask = $this->queue->getNext($this->agentId);
        
        $this->assertEquals($task1, $nextTask);
    }

    public function testGetByStatus(): void
    {
        $task1 = new Task('test.task', []);
        $task2 = new Task('test.task', []);
        
        $task1->assign($this->agentId);
        $task1->start();
        
        $this->queue->enqueue($task1);
        $this->queue->enqueue($task2);
        
        $runningTasks = $this->queue->getByStatus(Task::STATUS_RUNNING);
        $pendingTasks = $this->queue->getByStatus(Task::STATUS_PENDING);
        
        $this->assertEquals(1, $runningTasks->count());
        $this->assertEquals(1, $pendingTasks->count());
        $this->assertEquals($task1, $runningTasks->first());
        $this->assertEquals($task2, $pendingTasks->first());
    }

    public function testGetByAgent(): void
    {
        $task1 = new Task('test.task', []);
        $task2 = new Task('test.task', []);
        
        $task1->assign($this->agentId);
        
        $this->queue->enqueue($task1);
        $this->queue->enqueue($task2);
        
        $agentTasks = $this->queue->getByAgent($this->agentId);
        
        $this->assertEquals(1, $agentTasks->count());
        $this->assertEquals($task1, $agentTasks->first());
    }

    public function testGetByType(): void
    {
        $task1 = new Task('test.task1', []);
        $task2 = new Task('test.task2', []);
        
        $this->queue->enqueue($task1);
        $this->queue->enqueue($task2);
        
        $typeTasks = $this->queue->getByType('test.task1');
        
        $this->assertEquals(1, $typeTasks->count());
        $this->assertEquals($task1, $typeTasks->first());
    }

    public function testTaskUpdate(): void
    {
        Event::fake();
        
        $this->queue->enqueue($this->task);
        
        $this->task->assign($this->agentId);

        Log::shouldReceive('info')
            ->once()
            ->with("Task {$this->task->getId()} updated with status {$this->task->getStatus()}");

        $this->queue->update($this->task);
        
        Event::assertDispatched('mcp.task.updated', function ($eventName, $args) {
            return $args[0] === $this->task;
        });
        
        $updatedTask = $this->queue->get($this->task->getId());
        $this->assertEquals($this->agentId, $updatedTask->getAssignedAgentId());
    }

    public function testUpdateNonexistentTask(): void
    {
        $this->expectException(\InvalidArgumentException::class);
        $this->queue->update($this->task);
    }

    public function testClear(): void
    {
        $this->queue->enqueue($this->task);

        Log::shouldReceive('info')
            ->once()
            ->with('Task queue cleared');

        $this->queue->clear();
        
        $this->assertEquals(0, $this->queue->getAll()->count());
        $this->assertNull(Cache::get('mcp.task_queue'));
    }

    public function testCheckTimeouts(): void
    {
        Event::fake();
        
        $task = new Task('test.task', [], 0, 3, 1); // 1 second timeout
        $task->assign($this->agentId);
        $task->start();
        
        $this->queue->enqueue($task);
        sleep(2);

        Log::shouldReceive('info')
            ->once()
            ->with('Detected 1 timed out tasks');

        $this->queue->checkTimeouts();
        
        Event::assertDispatched('mcp.task.timeout', function ($eventName, $args) use ($task) {
            return $args[0] === $task;
        });
        
        $updatedTask = $this->queue->get($task->getId());
        $this->assertEquals(Task::STATUS_TIMEOUT, $updatedTask->getStatus());
    }

    public function testGetQueueStats(): void
    {
        $task1 = new Task('test.task', []); // pending
        
        $task2 = new Task('test.task', []); // running
        $task2->assign($this->agentId);
        $task2->start();
        
        $task3 = new Task('test.task', []); // completed
        $task3->assign($this->agentId);
        $task3->start();
        $task3->complete();
        
        $task4 = new Task('test.task', [], 0, 1); // failed
        $task4->assign($this->agentId);
        $task4->start();
        $task4->fail('Test error');
        
        $this->queue->enqueue($task1);
        $this->queue->enqueue($task2);
        $this->queue->enqueue($task3);
        $this->queue->enqueue($task4);
        
        $stats = $this->queue->getQueueStats();
        
        $this->assertEquals(4, $stats['total_tasks']);
        $this->assertEquals(1, $stats['pending_tasks']);
        $this->assertEquals(1, $stats['running_tasks']);
        $this->assertEquals(1, $stats['completed_tasks']);
        $this->assertEquals(1, $stats['failed_tasks']);
        $this->assertEquals(0, $stats['timeout_tasks']);
        $this->assertIsFloat($stats['average_completion_time']);
        $this->assertEquals(50.0, $stats['success_rate']); // 1 completed out of 2 finished tasks
    }

    public function testTaskPersistence(): void
    {
        $this->queue->enqueue($this->task);
        
        $newQueue = new TaskQueue();
        $loadedTask = $newQueue->get($this->task->getId());
        
        $this->assertEquals($this->task->getId(), $loadedTask->getId());
        $this->assertEquals($this->task->getType(), $loadedTask->getType());
        $this->assertEquals($this->task->getParameters(), $loadedTask->getParameters());
    }
} 