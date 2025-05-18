<?php

namespace Tests\Mcp\Console\Commands;

use Mcp\Console\Commands\McpStatus;
use Mcp\Discovery\ServiceRegistry;
use Mcp\Discovery\ServiceHealthMonitor;
use Tests\TestCase;
use Mockery;

class McpStatusTest extends TestCase
{
    private McpStatus $command;
    private ServiceRegistry $registry;
    private ServiceHealthMonitor $monitor;

    protected function setUp(): void
    {
        parent::setUp();
        
        $this->registry = Mockery::mock(ServiceRegistry::class);
        $this->monitor = Mockery::mock(ServiceHealthMonitor::class);
        
        $this->app->instance(ServiceRegistry::class, $this->registry);
        $this->app->instance(ServiceHealthMonitor::class, $this->monitor);
        
        $this->command = new McpStatus($this->registry, $this->monitor);
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

        $this->command->handle();
        
        $this->assertEquals(0, $this->command->getExitCode());
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

        $this->command->handle();
        
        $this->assertEquals(1, $this->command->getExitCode());
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

        $this->command->handle();
        
        $this->assertEquals(1, $this->command->getExitCode());
    }

    public function testHandleWithMultipleServices(): void
    {
        $services = [
            [
                'class' => 'App\\Services\\TestService1',
                'methods' => ['testMethod1'],
                'metadata' => ['type' => 'test']
            ],
            [
                'class' => 'App\\Services\\TestService2',
                'methods' => ['testMethod2'],
                'metadata' => ['type' => 'test']
            ]
        ];

        $this->registry->shouldReceive('getServices')
            ->once()
            ->andReturn($services);

        $this->monitor->shouldReceive('getMetrics')
            ->twice()
            ->andReturn([
                'calls' => 10,
                'successes' => 10,
                'errors' => 0,
                'response_time' => 100,
                'memory_usage' => 1024
            ]);

        $this->command->handle();
        
        $this->assertEquals(0, $this->command->getExitCode());
    }
} 