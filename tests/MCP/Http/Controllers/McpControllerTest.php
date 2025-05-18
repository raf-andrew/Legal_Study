<?php

namespace Tests\Mcp\Http\Controllers;

use Mcp\Http\Controllers\McpController;
use Mcp\Discovery\ServiceRegistry;
use Mcp\Discovery\ServiceHealthMonitor;
use Tests\TestCase;
use Illuminate\Support\Facades\Config;
use Mockery;

class McpControllerTest extends TestCase
{
    private McpController $controller;
    private ServiceRegistry $registry;
    private ServiceHealthMonitor $monitor;

    protected function setUp(): void
    {
        parent::setUp();
        
        $this->registry = Mockery::mock(ServiceRegistry::class);
        $this->monitor = Mockery::mock(ServiceHealthMonitor::class);
        
        $this->app->instance(ServiceRegistry::class, $this->registry);
        $this->app->instance(ServiceHealthMonitor::class, $this->monitor);
        
        $this->controller = new McpController($this->registry, $this->monitor);
    }

    protected function tearDown(): void
    {
        Mockery::close();
        parent::tearDown();
    }

    public function testDashboardWithNoServices(): void
    {
        $this->registry->shouldReceive('getServices')
            ->once()
            ->andReturn([]);

        $response = $this->controller->dashboard();
        
        $this->assertEquals(200, $response->getStatusCode());
        $this->assertViewIs('mcp::dashboard');
        $this->assertViewHas('services', []);
    }

    public function testDashboardWithServices(): void
    {
        $services = [
            [
                'class' => 'App\\Services\\TestService',
                'methods' => ['testMethod'],
                'metadata' => ['type' => 'test']
            ]
        ];

        $this->registry->shouldReceive('getServices')
            ->once()
            ->andReturn($services);

        $this->monitor->shouldReceive('getMetrics')
            ->once()
            ->with($services[0]['class'], $services[0]['methods'][0])
            ->andReturn([
                'calls' => 10,
                'successes' => 10,
                'errors' => 0,
                'response_time' => 100,
                'memory_usage' => 1024
            ]);

        $response = $this->controller->dashboard();
        
        $this->assertEquals(200, $response->getStatusCode());
        $this->assertViewIs('mcp::dashboard');
        $this->assertViewHas('services');
    }

    public function testServicesWithNoServices(): void
    {
        $this->registry->shouldReceive('getServices')
            ->once()
            ->andReturn([]);

        $response = $this->controller->services();
        
        $this->assertEquals(200, $response->getStatusCode());
        $this->assertViewIs('mcp::services');
        $this->assertViewHas('services', []);
    }

    public function testServicesWithServices(): void
    {
        $services = [
            [
                'class' => 'App\\Services\\TestService',
                'methods' => ['testMethod'],
                'metadata' => ['type' => 'test']
            ]
        ];

        $this->registry->shouldReceive('getServices')
            ->once()
            ->andReturn($services);

        $response = $this->controller->services();
        
        $this->assertEquals(200, $response->getStatusCode());
        $this->assertViewIs('mcp::services');
        $this->assertViewHas('services', $services);
    }

    public function testMonitoringWithNoServices(): void
    {
        $this->registry->shouldReceive('getServices')
            ->once()
            ->andReturn([]);

        $response = $this->controller->monitoring();
        
        $this->assertEquals(200, $response->getStatusCode());
        $this->assertViewIs('mcp::monitoring');
        $this->assertViewHas('services', []);
    }

    public function testMonitoringWithServices(): void
    {
        $services = [
            [
                'class' => 'App\\Services\\TestService',
                'methods' => ['testMethod'],
                'metadata' => ['type' => 'test']
            ]
        ];

        $this->registry->shouldReceive('getServices')
            ->once()
            ->andReturn($services);

        $this->monitor->shouldReceive('getMetrics')
            ->once()
            ->with($services[0]['class'], $services[0]['methods'][0])
            ->andReturn([
                'calls' => 10,
                'successes' => 10,
                'errors' => 0,
                'response_time' => 100,
                'memory_usage' => 1024
            ]);

        $response = $this->controller->monitoring();
        
        $this->assertEquals(200, $response->getStatusCode());
        $this->assertViewIs('mcp::monitoring');
        $this->assertViewHas('services');
    }

    public function testDiscover(): void
    {
        $services = [
            [
                'class' => 'App\\Services\\TestService',
                'methods' => ['testMethod'],
                'metadata' => ['type' => 'test']
            ]
        ];

        $this->registry->shouldReceive('clear')
            ->once();

        $this->registry->shouldReceive('register')
            ->once()
            ->with($services[0]);

        $response = $this->controller->discover($services);
        
        $this->assertEquals(200, $response->getStatusCode());
        $this->assertEquals(['message' => 'Services discovered successfully'], $response->getData(true));
    }

    public function testDiscoverWithError(): void
    {
        $services = [
            [
                'class' => 'InvalidService',
                'methods' => [],
                'metadata' => []
            ]
        ];

        $this->registry->shouldReceive('clear')
            ->once();

        $this->registry->shouldReceive('register')
            ->once()
            ->with($services[0])
            ->andThrow(new \InvalidArgumentException('Invalid service'));

        $response = $this->controller->discover($services);
        
        $this->assertEquals(400, $response->getStatusCode());
        $this->assertEquals(['error' => 'Invalid service'], $response->getData(true));
    }
} 