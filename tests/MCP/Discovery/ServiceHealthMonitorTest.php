<?php

namespace Tests\Mcp\Discovery;

use Mcp\Discovery\ServiceHealthMonitor;
use Tests\TestCase;
use Illuminate\Support\Facades\Cache;
use Mockery;

class ServiceHealthMonitorTest extends TestCase
{
    private ServiceHealthMonitor $monitor;

    protected function setUp(): void
    {
        parent::setUp();
        $this->monitor = new ServiceHealthMonitor();
    }

    public function testHealthMetricsRecording(): void
    {
        $serviceClass = 'App\\Services\\TestService';
        $method = 'testMethod';
        $startTime = microtime(true);
        $memoryUsage = memory_get_usage();

        $this->monitor->recordCall($serviceClass, $method, $startTime, $memoryUsage);
        
        $metrics = $this->monitor->getMetrics($serviceClass, $method);
        
        $this->assertIsArray($metrics);
        $this->assertEquals(1, $metrics['calls']);
        $this->assertEquals(1, $metrics['successes']);
        $this->assertEquals(0, $metrics['errors']);
        $this->assertGreaterThan(0, $metrics['response_time']);
        $this->assertGreaterThan(0, $metrics['memory_usage']);
    }

    public function testHealthThresholdWarnings(): void
    {
        $serviceClass = 'App\\Services\\TestService';
        $method = 'testMethod';
        $startTime = microtime(true);
        $memoryUsage = memory_get_usage();

        // Set low thresholds for testing
        $this->monitor->setResponseTimeThreshold(1);
        $this->monitor->setErrorRateThreshold(0.1);
        $this->monitor->setMemoryUsageThreshold(1024);

        // Record a slow call
        sleep(2);
        $this->monitor->recordCall($serviceClass, $method, $startTime, $memoryUsage);
        
        // Record an error
        $this->monitor->recordError($serviceClass, $method, new \Exception('Test error'));
        
        // Record high memory usage
        $this->monitor->recordCall($serviceClass, $method, $startTime, 2048);
        
        $metrics = $this->monitor->getMetrics($serviceClass, $method);
        
        $this->assertEquals(3, $metrics['calls']);
        $this->assertEquals(2, $metrics['successes']);
        $this->assertEquals(1, $metrics['errors']);
        $this->assertGreaterThan(1, $metrics['response_time']);
        $this->assertGreaterThan(1024, $metrics['memory_usage']);
    }

    public function testMetricsClearing(): void
    {
        $serviceClass = 'App\\Services\\TestService';
        $method = 'testMethod';
        $startTime = microtime(true);
        $memoryUsage = memory_get_usage();

        $this->monitor->recordCall($serviceClass, $method, $startTime, $memoryUsage);
        $this->monitor->clearMetrics();
        
        $metrics = $this->monitor->getMetrics($serviceClass, $method);
        
        $this->assertEmpty($metrics);
    }

    public function testThresholdConfiguration(): void
    {
        $this->monitor->setResponseTimeThreshold(1000);
        $this->monitor->setErrorRateThreshold(0.5);
        $this->monitor->setMemoryUsageThreshold(1024);
        
        $this->assertEquals(1000, $this->monitor->getResponseTimeThreshold());
        $this->assertEquals(0.5, $this->monitor->getErrorRateThreshold());
        $this->assertEquals(1024, $this->monitor->getMemoryUsageThreshold());
    }

    public function testCachePersistence(): void
    {
        $serviceClass = 'App\\Services\\TestService';
        $method = 'testMethod';
        $startTime = microtime(true);
        $memoryUsage = memory_get_usage();

        $this->monitor->recordCall($serviceClass, $method, $startTime, $memoryUsage);
        
        $newMonitor = new ServiceHealthMonitor();
        $metrics = $newMonitor->getMetrics($serviceClass, $method);
        
        $this->assertIsArray($metrics);
        $this->assertEquals(1, $metrics['calls']);
    }

    public function testCacheTTL(): void
    {
        $serviceClass = 'App\\Services\\TestService';
        $method = 'testMethod';
        $startTime = microtime(true);
        $memoryUsage = memory_get_usage();

        $this->monitor->recordCall($serviceClass, $method, $startTime, $memoryUsage);
        
        Cache::shouldReceive('get')
            ->once()
            ->with('mcp.metrics')
            ->andReturn(null);

        $newMonitor = new ServiceHealthMonitor();
        $metrics = $newMonitor->getMetrics($serviceClass, $method);
        
        $this->assertEmpty($metrics);
    }

    public function testErrorRecording(): void
    {
        $serviceClass = 'App\\Services\\TestService';
        $method = 'testMethod';
        $error = new \Exception('Test error');

        $this->monitor->recordError($serviceClass, $method, $error);
        
        $metrics = $this->monitor->getMetrics($serviceClass, $method);
        
        $this->assertEquals(1, $metrics['calls']);
        $this->assertEquals(0, $metrics['successes']);
        $this->assertEquals(1, $metrics['errors']);
    }
} 