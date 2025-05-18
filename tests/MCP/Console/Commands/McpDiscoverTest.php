<?php

namespace Tests\Mcp\Console\Commands;

use Mcp\Console\Commands\McpDiscover;
use Mcp\Discovery\Discovery;
use Mcp\Discovery\ServiceRegistry;
use Tests\TestCase;
use Illuminate\Support\Facades\Event;
use Mockery;

class McpDiscoverTest extends TestCase
{
    private McpDiscover $command;
    private Discovery $discovery;
    private ServiceRegistry $registry;

    protected function setUp(): void
    {
        parent::setUp();
        
        $this->discovery = Mockery::mock(Discovery::class);
        $this->registry = Mockery::mock(ServiceRegistry::class);
        
        $this->app->instance(Discovery::class, $this->discovery);
        $this->app->instance(ServiceRegistry::class, $this->registry);
        
        $this->command = new McpDiscover($this->discovery, $this->registry);
    }

    protected function tearDown(): void
    {
        Mockery::close();
        parent::tearDown();
    }

    public function testHandleWithNoServices(): void
    {
        $this->discovery->shouldReceive('scanServices')
            ->once()
            ->andReturn([]);

        $this->registry->shouldReceive('clear')
            ->once();

        $this->command->handle();
        
        $this->assertEquals(0, $this->command->getExitCode());
    }

    public function testHandleWithServices(): void
    {
        $services = [
            [
                'class' => 'App\\Services\\TestService',
                'methods' => ['testMethod'],
                'metadata' => ['type' => 'test']
            ]
        ];

        $this->discovery->shouldReceive('scanServices')
            ->once()
            ->andReturn($services);

        $this->registry->shouldReceive('clear')
            ->once();

        $this->registry->shouldReceive('register')
            ->once()
            ->with($services[0]);

        Event::fake();

        $this->command->handle();
        
        $this->assertEquals(0, $this->command->getExitCode());
        Event::assertDispatched(\Mcp\Events\ServiceDiscovered::class);
    }

    public function testHandleWithError(): void
    {
        $this->discovery->shouldReceive('scanServices')
            ->once()
            ->andThrow(new \Exception('Test error'));

        $this->registry->shouldReceive('clear')
            ->never();

        $this->command->handle();
        
        $this->assertEquals(1, $this->command->getExitCode());
    }

    public function testHandleWithInvalidService(): void
    {
        $services = [
            [
                'class' => 'InvalidService',
                'methods' => [],
                'metadata' => []
            ]
        ];

        $this->discovery->shouldReceive('scanServices')
            ->once()
            ->andReturn($services);

        $this->registry->shouldReceive('clear')
            ->once();

        $this->registry->shouldReceive('register')
            ->once()
            ->with($services[0])
            ->andThrow(new \InvalidArgumentException('Invalid service'));

        Event::fake();

        $this->command->handle();
        
        $this->assertEquals(0, $this->command->getExitCode());
        Event::assertNotDispatched(\Mcp\Events\ServiceDiscovered::class);
    }
} 