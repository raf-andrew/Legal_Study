<?php

namespace Tests\Mcp\Agent;

use Mcp\Agent\AgentManager;
use Mcp\Agent\Agent;
use Tests\TestCase;
use Illuminate\Support\Facades\Cache;
use Illuminate\Support\Facades\Log;
use Mockery;
use App\Mcp\Agent\AgentManagerInterface;

class AgentManagerTest extends TestCase
{
    protected AgentManagerInterface $manager;
    protected Agent $agent1;
    protected Agent $agent2;

    protected function setUp(): void
    {
        parent::setUp();
        
        Cache::flush();
        
        $this->manager = new AgentManager();
        $this->agent1 = new Agent('agent1', 'Agent One');
        $this->agent2 = new Agent('agent2', 'Agent Two');
    }

    public function test_register_and_get_agent(): void
    {
        $this->assertTrue($this->manager->registerAgent($this->agent1));
        $this->assertSame($this->agent1, $this->manager->getAgent('agent1'));
        $this->assertFalse($this->manager->registerAgent($this->agent1)); // duplicate
    }

    public function test_unregister_agent(): void
    {
        $this->manager->registerAgent($this->agent1);
        $this->assertTrue($this->manager->unregisterAgent('agent1'));
        $this->assertNull($this->manager->getAgent('agent1'));
        $this->assertFalse($this->manager->unregisterAgent('agent1'));
    }

    public function test_get_agents(): void
    {
        $this->manager->registerAgent($this->agent1);
        $this->manager->registerAgent($this->agent2);
        $agents = $this->manager->getAgents();
        $this->assertCount(2, $agents);
        $this->assertArrayHasKey('agent1', $agents);
        $this->assertArrayHasKey('agent2', $agents);
    }

    public function test_lifecycle_methods(): void
    {
        $this->manager->registerAgent($this->agent1);
        $this->assertTrue($this->manager->startAgent('agent1'));
        $this->assertEquals('running', $this->manager->getAgentStatus('agent1'));
        $this->assertTrue($this->manager->pauseAgent('agent1'));
        $this->assertEquals('paused', $this->manager->getAgentStatus('agent1'));
        $this->assertTrue($this->manager->resumeAgent('agent1'));
        $this->assertEquals('running', $this->manager->getAgentStatus('agent1'));
        $this->assertTrue($this->manager->stopAgent('agent1'));
        $this->assertEquals('stopped', $this->manager->getAgentStatus('agent1'));
    }

    public function test_send_and_broadcast_message(): void
    {
        $this->manager->registerAgent($this->agent1);
        $this->manager->registerAgent($this->agent2);
        $this->assertTrue($this->manager->sendMessageToAgent('agent1', 'hello'));
        $this->manager->broadcastMessage('broadcast');
        $this->assertTrue(true); // If no exception, pass
    }

    public function test_permissions_and_metadata(): void
    {
        $this->manager->registerAgent($this->agent1);
        $this->assertTrue($this->manager->setAgentPermissions('agent1', ['read']));
        $this->assertEquals(['read'], $this->manager->getAgentPermissions('agent1'));
        $this->assertTrue($this->manager->setAgentMetadata('agent1', ['role' => 'admin']));
        $this->assertEquals(['role' => 'admin'], $this->manager->getAgentMetadata('agent1'));
    }

    public function test_health(): void
    {
        $this->manager->registerAgent($this->agent1);
        $this->assertIsArray($this->manager->getAgentHealth('agent1'));
    }

    public function testGetByType(): void
    {
        $this->manager->registerAgent($this->agent1);
        $this->manager->registerAgent($this->agent2);
        
        $workers = $this->manager->getByType('worker');
        $monitors = $this->manager->getByType('monitor');
        
        $this->assertEquals(1, $workers->count());
        $this->assertEquals(1, $monitors->count());
        $this->assertEquals($this->agent1, $workers->first());
        $this->assertEquals($this->agent2, $monitors->first());
    }

    public function testGetByCapability(): void
    {
        $this->manager->registerAgent($this->agent1);
        $this->manager->registerAgent($this->agent2);
        
        $taskExecutors = $this->manager->getByCapability('task_execution');
        $monitors = $this->manager->getByCapability('monitoring');
        
        $this->assertEquals(1, $taskExecutors->count());
        $this->assertEquals(1, $monitors->count());
        $this->assertEquals($this->agent1, $taskExecutors->first());
        $this->assertEquals($this->agent2, $monitors->first());
    }

    public function testGetActive(): void
    {
        $this->manager->registerAgent($this->agent1);
        $this->manager->registerAgent($this->agent2);
        
        $this->agent1->deactivate();
        
        $activeAgents = $this->manager->getActive();
        
        $this->assertEquals(1, $activeAgents->count());
        $this->assertEquals($this->agent2, $activeAgents->first());
    }

    public function testActivateAll(): void
    {
        $this->manager->registerAgent($this->agent1);
        $this->manager->registerAgent($this->agent2);
        
        $this->agent1->deactivate();
        $this->agent2->deactivate();
        
        Log::shouldReceive('info')
            ->twice();

        $this->manager->activateAll();
        
        $this->assertTrue($this->agent1->isActive());
        $this->assertTrue($this->agent2->isActive());
    }

    public function testDeactivateAll(): void
    {
        $this->manager->registerAgent($this->agent1);
        $this->manager->registerAgent($this->agent2);
        
        Log::shouldReceive('info')
            ->twice();

        $this->manager->deactivateAll();
        
        $this->assertFalse($this->agent1->isActive());
        $this->assertFalse($this->agent2->isActive());
    }

    public function testClear(): void
    {
        $this->manager->registerAgent($this->agent1);
        $this->manager->registerAgent($this->agent2);

        Log::shouldReceive('info')
            ->once()
            ->with('All agents cleared');

        $this->manager->clear();
        
        $this->assertEquals(0, $this->manager->getAll()->count());
        $this->assertNull(Cache::get('mcp.agents'));
    }

    public function testGetAgentStates(): void
    {
        $this->manager->registerAgent($this->agent1);
        $this->manager->registerAgent($this->agent2);
        
        $states = $this->manager->getAgentStates();
        
        $this->assertCount(2, $states);
        $this->assertEquals($this->agent1->getId(), $states[0]['id']);
        $this->assertEquals($this->agent2->getId(), $states[1]['id']);
        $this->assertArrayHasKey('state', $states[0]);
        $this->assertArrayHasKey('state', $states[1]);
    }

    public function testGetSystemMetrics(): void
    {
        $this->manager->registerAgent($this->agent1);
        $this->manager->registerAgent($this->agent2);
        
        $this->agent1->incrementTasksCompleted();
        $this->agent1->recordError();
        $this->agent1->updateResourceUsage(100.0, 50.0);
        
        $this->agent2->incrementTasksCompleted();
        $this->agent2->incrementTasksCompleted();
        $this->agent2->updateResourceUsage(200.0, 75.0);
        
        $metrics = $this->manager->getSystemMetrics();
        
        $this->assertEquals(2, $metrics['total_agents']);
        $this->assertEquals(2, $metrics['active_agents']);
        $this->assertEquals(3, $metrics['total_tasks_completed']);
        $this->assertEquals(1, $metrics['total_errors']);
        $this->assertEquals(150.0, $metrics['average_memory_usage']);
        $this->assertEquals(62.5, $metrics['average_cpu_usage']);
    }

    public function testAgentPersistence(): void
    {
        $this->manager->registerAgent($this->agent1);
        
        $newManager = new AgentManager();
        $loadedAgent = $newManager->getAgent('agent1');
        
        $this->assertEquals($this->agent1->getId(), $loadedAgent->getId());
        $this->assertEquals($this->agent1->getName(), $loadedAgent->getName());
        $this->assertEquals($this->agent1->getType(), $loadedAgent->getType());
    }
} 