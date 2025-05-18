<?php

namespace Tests\Mcp\Agent;

use Tests\TestCase;
use Mcp\Agent\Agent;
use Mcp\Agent\AgentManager;
use Mcp\Agent\AgentLifecycleManager;
use Illuminate\Support\Facades\Cache;
use Illuminate\Support\Facades\Event;
use Mcp\Events\AgentLifecycleEvent;
use Mcp\Events\AgentStateChanged;
use Mcp\Events\AgentErrorOccurred;
use Mcp\Events\AgentResourceUsageUpdated;

class AgentLifecycleManagerTest extends TestCase
{
    protected AgentManager $agentManager;
    protected AgentLifecycleManager $lifecycleManager;
    protected Agent $testAgent;

    protected function setUp(): void
    {
        parent::setUp();
        
        $this->agentManager = new AgentManager();
        $this->lifecycleManager = new AgentLifecycleManager($this->agentManager);
        
        $this->testAgent = new Agent('Test Agent', 'test', ['test_capability']);
        
        Cache::forget('mcp.agent.lifecycle');
        Event::fake();
    }

    public function test_initialize_agent(): void
    {
        $this->lifecycleManager->initialize($this->testAgent);
        
        $state = $this->lifecycleManager->getLifecycleState($this->testAgent->getId());
        $this->assertNotNull($state);
        $this->assertEquals('initialized', $state['status']);
        $this->assertEquals(0, $state['error_count']);
        $this->assertEquals('healthy', $state['health_status']);
        
        Event::assertDispatched(AgentLifecycleEvent::class, function ($event) {
            return $event->agent->getId() === $this->testAgent->getId() &&
                   $event->event === 'initialized';
        });
    }

    public function test_activate_agent(): void
    {
        $this->lifecycleManager->initialize($this->testAgent);
        $this->lifecycleManager->activate($this->testAgent);
        
        $state = $this->lifecycleManager->getLifecycleState($this->testAgent->getId());
        $this->assertEquals('active', $state['status']);
        $this->assertNotNull($state['activated_at']);
        
        Event::assertDispatched(AgentStateChanged::class, function ($event) {
            return $event->agent->getId() === $this->testAgent->getId() &&
                   $event->data['new_state'] === 'active';
        });
    }

    public function test_deactivate_agent(): void
    {
        $this->lifecycleManager->initialize($this->testAgent);
        $this->lifecycleManager->activate($this->testAgent);
        $this->lifecycleManager->deactivate($this->testAgent);
        
        $state = $this->lifecycleManager->getLifecycleState($this->testAgent->getId());
        $this->assertEquals('inactive', $state['status']);
        $this->assertNotNull($state['deactivated_at']);
        
        Event::assertDispatched(AgentStateChanged::class, function ($event) {
            return $event->agent->getId() === $this->testAgent->getId() &&
                   $event->data['new_state'] === 'inactive';
        });
    }

    public function test_cleanup_agent(): void
    {
        $this->lifecycleManager->initialize($this->testAgent);
        $this->lifecycleManager->cleanup($this->testAgent);
        
        $state = $this->lifecycleManager->getLifecycleState($this->testAgent->getId());
        $this->assertNull($state);
        
        Event::assertDispatched(AgentLifecycleEvent::class, function ($event) {
            return $event->agent->getId() === $this->testAgent->getId() &&
                   $event->event === 'cleaned_up';
        });
    }

    public function test_record_error(): void
    {
        $this->lifecycleManager->initialize($this->testAgent);
        
        $error = new \RuntimeException('Test error');
        $this->lifecycleManager->recordError($this->testAgent, $error);
        
        $state = $this->lifecycleManager->getLifecycleState($this->testAgent->getId());
        $this->assertEquals(1, $state['error_count']);
        $this->assertEquals('Test error', $state['last_error']['message']);
        
        Event::assertDispatched(AgentErrorOccurred::class, function ($event) use ($error) {
            return $event->agent->getId() === $this->testAgent->getId() &&
                   $event->data['message'] === $error->getMessage();
        });
    }

    public function test_update_resource_usage(): void
    {
        $this->lifecycleManager->initialize($this->testAgent);
        
        $memoryUsage = 1024.5;
        $cpuUsage = 25.3;
        $this->lifecycleManager->updateResourceUsage($this->testAgent, $memoryUsage, $cpuUsage);
        
        $state = $this->lifecycleManager->getLifecycleState($this->testAgent->getId());
        $this->assertEquals($memoryUsage, $state['resource_usage']['memory']);
        $this->assertEquals($cpuUsage, $state['resource_usage']['cpu']);
        
        Event::assertDispatched(AgentResourceUsageUpdated::class, function ($event) use ($memoryUsage, $cpuUsage) {
            return $event->agent->getId() === $this->testAgent->getId() &&
                   $event->data['memory_usage'] === $memoryUsage &&
                   $event->data['cpu_usage'] === $cpuUsage;
        });
    }

    public function test_update_health_status(): void
    {
        $this->lifecycleManager->initialize($this->testAgent);
        
        $newStatus = 'degraded';
        $this->lifecycleManager->updateHealthStatus($this->testAgent, $newStatus);
        
        $state = $this->lifecycleManager->getLifecycleState($this->testAgent->getId());
        $this->assertEquals($newStatus, $state['health_status']);
    }

    public function test_initialize_already_initialized_agent(): void
    {
        $this->lifecycleManager->initialize($this->testAgent);
        
        $this->expectException(\InvalidArgumentException::class);
        $this->expectExceptionMessage("Agent {$this->testAgent->getId()} is already initialized");
        
        $this->lifecycleManager->initialize($this->testAgent);
    }

    public function test_activate_uninitialized_agent(): void
    {
        $this->expectException(\InvalidArgumentException::class);
        $this->expectExceptionMessage("Agent {$this->testAgent->getId()} must be initialized first");
        
        $this->lifecycleManager->activate($this->testAgent);
    }

    public function test_deactivate_uninitialized_agent(): void
    {
        $this->expectException(\InvalidArgumentException::class);
        $this->expectExceptionMessage("Agent {$this->testAgent->getId()} not found");
        
        $this->lifecycleManager->deactivate($this->testAgent);
    }

    public function test_cleanup_uninitialized_agent(): void
    {
        $this->expectException(\InvalidArgumentException::class);
        $this->expectExceptionMessage("Agent {$this->testAgent->getId()} not found");
        
        $this->lifecycleManager->cleanup($this->testAgent);
    }

    public function test_record_error_uninitialized_agent(): void
    {
        $this->expectException(\InvalidArgumentException::class);
        $this->expectExceptionMessage("Agent {$this->testAgent->getId()} not found");
        
        $this->lifecycleManager->recordError($this->testAgent, new \RuntimeException('Test error'));
    }

    public function test_update_resource_usage_uninitialized_agent(): void
    {
        $this->expectException(\InvalidArgumentException::class);
        $this->expectExceptionMessage("Agent {$this->testAgent->getId()} not found");
        
        $this->lifecycleManager->updateResourceUsage($this->testAgent, 1024.5, 25.3);
    }

    public function test_update_health_status_uninitialized_agent(): void
    {
        $this->expectException(\InvalidArgumentException::class);
        $this->expectExceptionMessage("Agent {$this->testAgent->getId()} not found");
        
        $this->lifecycleManager->updateHealthStatus($this->testAgent, 'degraded');
    }
} 