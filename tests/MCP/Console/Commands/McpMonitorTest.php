<?php

namespace Tests\Mcp\Console\Commands;

use Mcp\Console\Commands\McpMonitor;
use Mcp\Discovery\ServiceRegistry;
use Mcp\Discovery\ServiceHealthMonitor;
use Tests\TestCase;
use Illuminate\Support\Facades\Event;
use Mockery;

class McpMonitorTest extends TestCase
{
    private McpMonitor $command;
    private ServiceRegistry $registry;
    private ServiceHealthMonitor $monitor;

    protected function setUp(): void
    {
        parent::setUp();
        
        $this->registry = Mockery::mock(ServiceRegistry::class);
        $this->monitor = Mockery::mock(ServiceHealthMonitor::class);
        
        $this->app->instance(ServiceRegistry::class, $this->registry);
        $this->app->instance(ServiceHealthMonitor::class, $this->monitor);
        
        $this->command = new McpMonitor($this->registry, $this->monitor);
    }

    protected function tearDown(): void
    {
        Mockery::close();
        parent::tearDown();
    }

    public function testHandleWithNoServices(): void
    {
        $this->registry->shouldReceive('getServices')
            ->once()
            ->andReturn([]);

        $this->command->handle();
        
        $this->assertEquals(0, $this->command->getExitCode());
    }

    public function testHandleWithHealthyServices(): void
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

        Event::fake();

        $this->command->handle();
        
        $this->assertEquals(0, $this->command->getExitCode());
        Event::assertDispatched(\Mcp\Events\ServiceHealthChanged::class);
    }

    public function testHandleWithUnhealthyServices(): void
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
                'successes' => 5,
                'errors' => 5,
                'response_time' => 1000,
                'memory_usage' => 2048
            ]);

        Event::fake();

        $this->command->handle();
        
        $this->assertEquals(1, $this->command->getExitCode());
        Event::assertDispatched(\Mcp\Events\ServiceHealthChanged::class);
    }

    public function testHandleWithError(): void
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
            ->andThrow(new \Exception('Test error'));

        Event::fake();

        $this->command->handle();
        
        $this->assertEquals(1, $this->command->getExitCode());
        Event::assertDispatched(\Mcp\Events\ServiceError::class);
    }
} 