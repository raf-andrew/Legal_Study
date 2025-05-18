<?php

namespace Tests\Mcp\Agent\Task;

use Mcp\Agent\Task\Task;
use Tests\TestCase;

class TaskTest extends TestCase
{
    private Task $task;
    private string $type = 'test.task';
    private array $parameters = ['key' => 'value'];
    private string $agentId = 'agent-123';

    protected function setUp(): void
    {
        parent::setUp();
        $this->task = new Task($this->type, $this->parameters);
    }

    public function testTaskConstruction(): void
    {
        $this->assertNotEmpty($this->task->getId());
        $this->assertEquals($this->type, $this->task->getType());
        $this->assertEquals($this->parameters, $this->task->getParameters());
        $this->assertEquals(Task::STATUS_PENDING, $this->task->getStatus());
        $this->assertNull($this->task->getAssignedAgentId());
        $this->assertEquals(0, $this->task->getPriority());
        $this->assertIsInt($this->task->getCreatedAt());
        $this->assertNull($this->task->getStartedAt());
        $this->assertNull($this->task->getCompletedAt());
        $this->assertEmpty($this->task->getResult());
        $this->assertEmpty($this->task->getErrors());
        $this->assertEquals(0, $this->task->getAttempts());
        $this->assertEquals(3, $this->task->getMaxAttempts());
        $this->assertEquals(3600, $this->task->getTimeout());
    }

    public function testTaskAssignment(): void
    {
        $this->task->assign($this->agentId);
        
        $this->assertEquals($this->agentId, $this->task->getAssignedAgentId());
        $this->assertEquals(Task::STATUS_ASSIGNED, $this->task->getStatus());
    }

    public function testTaskStart(): void
    {
        $this->task->assign($this->agentId);
        $this->task->start();
        
        $this->assertEquals(Task::STATUS_RUNNING, $this->task->getStatus());
        $this->assertEquals(1, $this->task->getAttempts());
        $this->assertIsInt($this->task->getStartedAt());
    }

    public function testTaskStartWithoutAssignment(): void
    {
        $this->expectException(\RuntimeException::class);
        $this->expectExceptionMessage('Task must be assigned before starting');
        
        $this->task->start();
    }

    public function testTaskCompletion(): void
    {
        $result = ['status' => 'success'];
        
        $this->task->assign($this->agentId);
        $this->task->start();
        $this->task->complete($result);
        
        $this->assertEquals(Task::STATUS_COMPLETED, $this->task->getStatus());
        $this->assertEquals($result, $this->task->getResult());
        $this->assertIsInt($this->task->getCompletedAt());
    }

    public function testTaskCompletionWithoutRunning(): void
    {
        $this->expectException(\RuntimeException::class);
        $this->expectExceptionMessage('Task must be running before completing');
        
        $this->task->complete();
    }

    public function testTaskFailure(): void
    {
        $this->task->assign($this->agentId);
        $this->task->start();
        $this->task->fail('Test error');
        
        $this->assertEquals(Task::STATUS_PENDING, $this->task->getStatus());
        $this->assertNull($this->task->getAssignedAgentId());
        $this->assertEquals(1, count($this->task->getErrors()));
        $this->assertEquals('Test error', $this->task->getErrors()[0]['message']);
    }

    public function testTaskFailureAfterMaxAttempts(): void
    {
        $this->task = new Task($this->type, $this->parameters, 0, 1); // max 1 attempt
        
        $this->task->assign($this->agentId);
        $this->task->start();
        $this->task->fail('Test error');
        
        $this->assertEquals(Task::STATUS_FAILED, $this->task->getStatus());
        $this->assertEquals(1, count($this->task->getErrors()));
    }

    public function testTaskTimeout(): void
    {
        $this->task = new Task($this->type, $this->parameters, 0, 3, 1); // 1 second timeout
        
        $this->task->assign($this->agentId);
        $this->task->start();
        sleep(2);
        $this->task->timeout();
        
        $this->assertEquals(Task::STATUS_TIMEOUT, $this->task->getStatus());
        $this->assertEquals(1, count($this->task->getErrors()));
        $this->assertEquals('Task timed out', $this->task->getErrors()[0]['message']);
    }

    public function testCanRetry(): void
    {
        $this->assertTrue($this->task->canRetry());
        
        $this->task->assign($this->agentId);
        $this->task->start();
        $this->task->complete();
        
        $this->assertFalse($this->task->canRetry());
    }

    public function testJsonSerialization(): void
    {
        $this->task->assign($this->agentId);
        $this->task->start();
        
        $json = json_encode($this->task);
        $data = json_decode($json, true);
        
        $this->assertArrayHasKey('id', $data);
        $this->assertArrayHasKey('type', $data);
        $this->assertArrayHasKey('parameters', $data);
        $this->assertArrayHasKey('status', $data);
        $this->assertArrayHasKey('assigned_agent_id', $data);
        $this->assertArrayHasKey('priority', $data);
        $this->assertArrayHasKey('created_at', $data);
        $this->assertArrayHasKey('started_at', $data);
        $this->assertArrayHasKey('completed_at', $data);
        $this->assertArrayHasKey('result', $data);
        $this->assertArrayHasKey('errors', $data);
        $this->assertArrayHasKey('attempts', $data);
        $this->assertArrayHasKey('max_attempts', $data);
        $this->assertArrayHasKey('timeout', $data);
        
        $this->assertEquals($this->type, $data['type']);
        $this->assertEquals($this->parameters, $data['parameters']);
        $this->assertEquals($this->agentId, $data['assigned_agent_id']);
    }

    public function testFromArray(): void
    {
        $data = [
            'id' => 'test-id',
            'type' => $this->type,
            'parameters' => $this->parameters,
            'status' => Task::STATUS_RUNNING,
            'assigned_agent_id' => $this->agentId,
            'priority' => 1,
            'created_at' => time(),
            'started_at' => time(),
            'completed_at' => null,
            'result' => [],
            'errors' => [],
            'attempts' => 1,
            'max_attempts' => 3,
            'timeout' => 3600
        ];
        
        $task = Task::fromArray($data);
        
        $this->assertEquals($data['id'], $task->getId());
        $this->assertEquals($data['type'], $task->getType());
        $this->assertEquals($data['parameters'], $task->getParameters());
        $this->assertEquals($data['status'], $task->getStatus());
        $this->assertEquals($data['assigned_agent_id'], $task->getAssignedAgentId());
        $this->assertEquals($data['priority'], $task->getPriority());
        $this->assertEquals($data['created_at'], $task->getCreatedAt());
        $this->assertEquals($data['started_at'], $task->getStartedAt());
        $this->assertEquals($data['completed_at'], $task->getCompletedAt());
        $this->assertEquals($data['result'], $task->getResult());
        $this->assertEquals($data['errors'], $task->getErrors());
        $this->assertEquals($data['attempts'], $task->getAttempts());
    }

    public function testFromArrayWithDefaults(): void
    {
        $data = [
            'id' => 'test-id',
            'type' => $this->type,
            'status' => Task::STATUS_PENDING,
            'assigned_agent_id' => null,
            'created_at' => time(),
            'started_at' => null,
            'completed_at' => null,
            'result' => [],
            'errors' => [],
            'attempts' => 0
        ];
        
        $task = Task::fromArray($data);
        
        $this->assertEquals([], $task->getParameters());
        $this->assertEquals(0, $task->getPriority());
        $this->assertEquals(3, $task->getMaxAttempts());
        $this->assertEquals(3600, $task->getTimeout());
    }
} 