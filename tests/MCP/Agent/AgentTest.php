<?php

namespace Tests\Mcp\Agent;

use App\Mcp\Agent\Agent;
use App\Mcp\Agent\AgentInterface;
use PHPUnit\Framework\TestCase;
use Illuminate\Support\Facades\Cache;
use Illuminate\Support\Facades\Log;
use Mockery;
use Mcp\Agent\AbstractAgent;
use Mcp\Logging\LoggerInterface;
use Mcp\Security\PermissionManagerInterface;

class TestAgent extends AbstractAgent
{
    public function execute(array $parameters): array
    {
        $this->validatePermissions();
        $this->updateStatus(['last_execution' => date('Y-m-d H:i:s')]);
        return ['success' => true];
    }
}

class AgentTest extends TestCase
{
    protected AgentInterface $agent;
    private array $capabilities;
    private LoggerInterface $logger;
    private PermissionManagerInterface $permissionManager;
    private TestAgent $testAgent;

    protected function setUp(): void
    {
        parent::setUp();
        $this->agent = new Agent('agent1', 'Test Agent', ['role' => 'test']);
        $this->capabilities = ['task_execution', 'service_discovery', 'monitoring'];
        
        Cache::flush();

        $this->logger = $this->createMock(LoggerInterface::class);
        $this->permissionManager = $this->createMock(PermissionManagerInterface::class);
        $this->testAgent = new TestAgent($this->logger, $this->permissionManager);
    }

    public function test_interface_implementation(): void
    {
        $this->assertInstanceOf(AgentInterface::class, $this->agent);
    }

    public function test_getters(): void
    {
        $this->assertEquals('agent1', $this->agent->getId());
        $this->assertEquals('Test Agent', $this->agent->getName());
        $this->assertEquals('created', $this->agent->getStatus());
        $this->assertEquals(['role' => 'test'], $this->agent->getMetadata());
    }

    public function test_lifecycle_methods(): void
    {
        $this->assertTrue($this->agent->start());
        $this->assertEquals('running', $this->agent->getStatus());
        $this->assertTrue($this->agent->pause());
        $this->assertEquals('paused', $this->agent->getStatus());
        $this->assertTrue($this->agent->resume());
        $this->assertEquals('running', $this->agent->getStatus());
        $this->assertTrue($this->agent->stop());
        $this->assertEquals('stopped', $this->agent->getStatus());
    }

    public function test_permissions(): void
    {
        $this->assertEquals([], $this->agent->getPermissions());
        $this->assertTrue($this->agent->setPermissions(['read', 'write']));
        $this->assertEquals(['read', 'write'], $this->agent->getPermissions());
    }

    public function test_metadata(): void
    {
        $this->assertTrue($this->agent->setMetadata(['role' => 'admin']));
        $this->assertEquals(['role' => 'admin'], $this->agent->getMetadata());
    }

    public function test_health(): void
    {
        $this->assertIsArray($this->agent->getHealth());
    }

    public function test_message_methods(): void
    {
        $this->assertTrue($this->agent->sendMessage('hello'));
        $this->assertTrue($this->agent->receiveMessage('hello'));
    }

    public function testAgentConstruction(): void
    {
        $this->assertNotEmpty($this->agent->getId());
        $this->assertEquals('Test Agent', $this->agent->getName());
        $this->assertEquals('created', $this->agent->getStatus());
        $this->assertEquals(['role' => 'test'], $this->agent->getMetadata());
        $this->assertTrue($this->agent->isActive());
        
        $state = $this->agent->getState();
        $this->assertEquals('initialized', $state['status']);
        $this->assertEquals(0, $state['tasks_completed']);
        $this->assertEquals(0, $state['errors']);
    }

    public function testCapabilityChecking(): void
    {
        $this->assertTrue($this->agent->hasCapability('task_execution'));
        $this->assertFalse($this->agent->hasCapability('invalid_capability'));
    }

    public function testAgentActivation(): void
    {
        Log::shouldReceive('info')
            ->once()
            ->with('Agent Test Agent activated');

        $this->agent->activate();
        
        $this->assertTrue($this->agent->isActive());
        $this->assertEquals('active', $this->agent->getState()['status']);
    }

    public function testAgentDeactivation(): void
    {
        Log::shouldReceive('info')
            ->once()
            ->with('Agent Test Agent deactivated');

        $this->agent->deactivate();
        
        $this->assertFalse($this->agent->isActive());
        $this->assertEquals('inactive', $this->agent->getState()['status']);
    }

    public function testStateUpdates(): void
    {
        $this->agent->updateState('custom_key', 'custom_value');
        
        $state = $this->agent->getState();
        $this->assertEquals('custom_value', $state['custom_key']);
        
        $cachedState = Cache::get("mcp.agent.{$this->agent->getId()}.state");
        $this->assertEquals($state, $cachedState);
    }

    public function testTaskCompletion(): void
    {
        $this->agent->incrementTasksCompleted();
        $this->agent->incrementTasksCompleted();
        
        $this->assertEquals(2, $this->agent->getState()['tasks_completed']);
    }

    public function testErrorRecording(): void
    {
        $this->agent->recordError();
        $this->agent->recordError();
        $this->agent->recordError();
        
        $this->assertEquals(3, $this->agent->getState()['errors']);
    }

    public function testResourceUsageUpdates(): void
    {
        $memoryUsage = 1024.5;
        $cpuUsage = 45.7;
        
        $this->agent->updateResourceUsage($memoryUsage, $cpuUsage);
        
        $state = $this->agent->getState();
        $this->assertEquals($memoryUsage, $state['memory_usage']);
        $this->assertEquals($cpuUsage, $state['cpu_usage']);
    }

    public function testStatePersistence(): void
    {
        $this->agent->updateState('test_key', 'test_value');
        
        $newAgent = new Agent('agent1', 'Test Agent');
        $cachedState = Cache::get("mcp.agent.{$this->agent->getId()}.state");
        
        $this->assertEquals('test_value', $cachedState['test_key']);
    }

    public function testToArray(): void
    {
        $array = $this->agent->toArray();
        
        $this->assertArrayHasKey('id', $array);
        $this->assertArrayHasKey('name', $array);
        $this->assertArrayHasKey('type', $array);
        $this->assertArrayHasKey('capabilities', $array);
        $this->assertArrayHasKey('state', $array);
        $this->assertArrayHasKey('active', $array);
        
        $this->assertEquals('agent1', $array['id']);
        $this->assertEquals('Test Agent', $array['name']);
        $this->assertEquals('created', $array['type']);
        $this->assertEquals(['role' => 'test'], $array['metadata']);
        $this->assertEquals($this->capabilities, $array['capabilities']);
        $this->assertTrue($array['active']);
    }

    public function testAgentImplementsInterface(): void
    {
        $this->assertInstanceOf(AgentInterface::class, $this->testAgent);
    }

    public function testAgentInitialization(): void
    {
        $config = ['custom_setting' => 'value'];
        $this->testAgent->initialize($config);
        $status = $this->testAgent->getStatus();
        
        $this->assertTrue($status['initialized']);
        $this->assertEquals(0, $status['error_count']);
        $this->assertEquals(0, $status['success_count']);
    }

    public function testAgentExecution(): void
    {
        $this->permissionManager->method('hasPermissions')
            ->willReturn(true);

        $result = $this->testAgent->execute([]);
        $status = $this->testAgent->getStatus();

        $this->assertTrue($result['success']);
        $this->assertNotNull($status['last_execution']);
    }

    public function testAgentErrorHandling(): void
    {
        $error = new \RuntimeException('Test error');
        $this->testAgent->handleError($error);
        $status = $this->testAgent->getStatus();

        $this->assertEquals(1, $status['error_count']);
    }

    public function testAgentPermissionValidation(): void
    {
        $this->permissionManager->method('hasPermissions')
            ->willReturn(false);

        $this->expectException(\RuntimeException::class);
        $this->testAgent->execute([]);
    }

    public function testAgentAuditLogging(): void
    {
        $action = 'test_action';
        $details = ['test' => 'value'];
        
        $this->testAgent->logAuditEntry($action, $details);
        $auditLog = $this->testAgent->getAuditLog();
        
        $this->assertCount(1, $auditLog);
        $this->assertEquals($action, $auditLog[0]['action']);
        $this->assertEquals($details, $auditLog[0]['details']);
    }
} 