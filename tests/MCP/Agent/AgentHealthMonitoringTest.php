<?php

namespace Tests\MCP\Agent;

use Mcp\Agent\Agent;
use Mcp\Agent\AgentManager;
use Mcp\Agent\AgentLifecycleManager;
use Mcp\Events\AgentLifecycleEvent;
use Mcp\Events\AgentStateChanged;
use Mcp\Events\AgentErrorOccurred;
use Mcp\Events\AgentResourceUsageUpdated;
use PHPUnit\Framework\TestCase;
use Psr\SimpleCache\CacheInterface;
use Psr\Log\LoggerInterface;

class AgentHealthMonitoringTest extends TestCase
{
    protected AgentManager $agentManager;
    protected AgentLifecycleManager $lifecycleManager;
    protected Agent $testAgent;
    protected array $healthMetrics;
    protected TestCache $cache;
    protected LoggerInterface $logger;

    protected function setUp(): void
    {
        parent::setUp();

        // Create test cache
        $this->cache = new TestCache();

        // Create mock logger
        $this->logger = $this->createMock(LoggerInterface::class);
        $this->logger->method('info')
            ->willReturnCallback(function () {});
        $this->logger->method('error')
            ->willReturnCallback(function () {});
        $this->logger->method('debug')
            ->willReturnCallback(function () {});

        $this->agentManager = new AgentManager($this->cache, $this->logger);
        $this->lifecycleManager = new AgentLifecycleManager($this->agentManager, $this->cache, $this->logger);
        $this->testAgent = new Agent('test-agent', 'Test Agent', ['test_capability'], $this->cache, $this->logger);

        $this->healthMetrics = [
            'memory_threshold' => 80.0, // 80% memory usage threshold
            'cpu_threshold' => 70.0,    // 70% CPU usage threshold
            'error_threshold' => 3,     // Maximum number of errors before unhealthy
            'heartbeat_timeout' => 30   // Seconds before heartbeat timeout
        ];
    }

    public function testInitialHealthStatus(): void
    {
        $this->agentManager->register($this->testAgent);
        $this->lifecycleManager->initialize($this->testAgent);

        $state = $this->lifecycleManager->getLifecycleState($this->testAgent->getId());
        $this->assertNotNull($state);
        $this->assertEquals('healthy', $state['health_status']);
    }

    public function testHealthStatusUpdates(): void
    {
        $this->agentManager->register($this->testAgent);
        $this->lifecycleManager->initialize($this->testAgent);

        // Test degraded state
        $this->lifecycleManager->updateHealthStatus($this->testAgent, 'degraded');
        $state = $this->lifecycleManager->getLifecycleState($this->testAgent->getId());
        $this->assertEquals('degraded', $state['health_status']);

        // Test unhealthy state
        $this->lifecycleManager->updateHealthStatus($this->testAgent, 'unhealthy');
        $state = $this->lifecycleManager->getLifecycleState($this->testAgent->getId());
        $this->assertEquals('unhealthy', $state['health_status']);
    }

    public function testResourceUsageMonitoring(): void
    {
        $this->agentManager->register($this->testAgent);
        $this->lifecycleManager->initialize($this->testAgent);

        // Test memory usage
        $this->lifecycleManager->updateResourceUsage($this->testAgent, 85.0, 50.0);
        $state = $this->lifecycleManager->getLifecycleState($this->testAgent->getId());
        $this->assertEquals(85.0, $state['resource_usage']['memory']);
        $this->assertEquals(50.0, $state['resource_usage']['cpu']);
    }

    public function testErrorTracking(): void
    {
        $this->agentManager->register($this->testAgent);
        $this->lifecycleManager->initialize($this->testAgent);

        $error = new \Exception('Test error');
        $this->lifecycleManager->recordError($this->testAgent, $error);
        $state = $this->lifecycleManager->getLifecycleState($this->testAgent->getId());
        $this->assertEquals(1, $state['error_count']);
        $this->assertEquals('Test error', $state['last_error']['message']);
    }

    public function testHeartbeatMonitoring(): void
    {
        $this->agentManager->register($this->testAgent);
        $this->lifecycleManager->initialize($this->testAgent);

        $initialState = $this->lifecycleManager->getLifecycleState($this->testAgent->getId());
        $initialHeartbeat = $initialState['last_heartbeat'];

        sleep(1); // Wait a second
        $this->lifecycleManager->updateHeartbeat($this->testAgent);

        $newState = $this->lifecycleManager->getLifecycleState($this->testAgent->getId());
        $this->assertGreaterThan($initialHeartbeat, $newState['last_heartbeat']);
    }

    public function testHealthThresholds(): void
    {
        $this->agentManager->register($this->testAgent);
        $this->lifecycleManager->initialize($this->testAgent);

        // Test memory threshold
        $this->lifecycleManager->updateResourceUsage($this->testAgent, $this->healthMetrics['memory_threshold'] + 1, 50.0);
        $state = $this->lifecycleManager->getLifecycleState($this->testAgent->getId());
        $this->assertGreaterThan($this->healthMetrics['memory_threshold'], $state['resource_usage']['memory']);

        // Test CPU threshold
        $this->lifecycleManager->updateResourceUsage($this->testAgent, 50.0, $this->healthMetrics['cpu_threshold'] + 1);
        $state = $this->lifecycleManager->getLifecycleState($this->testAgent->getId());
        $this->assertGreaterThan($this->healthMetrics['cpu_threshold'], $state['resource_usage']['cpu']);
    }

    public function testHealthRecovery(): void
    {
        $this->agentManager->register($this->testAgent);
        $this->lifecycleManager->initialize($this->testAgent);

        // Set to unhealthy
        $this->lifecycleManager->updateHealthStatus($this->testAgent, 'unhealthy');
        $state = $this->lifecycleManager->getLifecycleState($this->testAgent->getId());
        $this->assertEquals('unhealthy', $state['health_status']);

        // Recover to healthy
        $this->lifecycleManager->updateHealthStatus($this->testAgent, 'healthy');
        $state = $this->lifecycleManager->getLifecycleState($this->testAgent->getId());
        $this->assertEquals('healthy', $state['health_status']);
    }

    public function testHealthPersistence(): void
    {
        $this->agentManager->register($this->testAgent);
        $this->lifecycleManager->initialize($this->testAgent);

        // Set some state
        $this->lifecycleManager->updateHealthStatus($this->testAgent, 'degraded');
        $this->lifecycleManager->updateResourceUsage($this->testAgent, 75.0, 60.0);

        // Create new instance to test persistence
        $newLifecycleManager = new AgentLifecycleManager($this->agentManager, $this->cache, $this->logger);
        $state = $newLifecycleManager->getLifecycleState($this->testAgent->getId());

        $this->assertNotNull($state);
        $this->assertEquals('degraded', $state['health_status']);
        $this->assertEquals(75.0, $state['resource_usage']['memory']);
        $this->assertEquals(60.0, $state['resource_usage']['cpu']);
    }
}
