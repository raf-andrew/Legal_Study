<?php

namespace Tests\Unit\Mcp\Console\Commands;

use App\Mcp\ConfigurationManager;
use App\Mcp\Console\Commands\ServerCommand;
use App\Mcp\EventBus;
use App\Mcp\Server;
use Illuminate\Support\Facades\Artisan;
use Tests\TestCase;

class ServerCommandTest extends TestCase
{
    protected $server;
    protected $configManager;
    protected $eventBus;

    protected function setUp(): void
    {
        parent::setUp();

        $this->configManager = $this->createMock(ConfigurationManager::class);
        $this->eventBus = $this->createMock(EventBus::class);
        $this->server = $this->createMock(Server::class);

        $this->server->method('isEnabled')->willReturn(true);
        $this->server->method('isDevelopment')->willReturn(true);
        $this->server->method('getEventBus')->willReturn($this->eventBus);
        $this->server->method('getService')
            ->with(ConfigurationManager::class)
            ->willReturn($this->configManager);

        $this->app->instance(Server::class, $this->server);
    }

    public function testShowStatus()
    {
        $this->server->method('getServices')->willReturn([
            'service1' => new \stdClass(),
            'service2' => new \stdClass(),
        ]);

        $exitCode = $this->artisan('mcp:server', [
            'action' => 'status',
            '--format' => 'json'
        ]);

        $this->assertEquals(0, $exitCode);
        $output = Artisan::output();
        
        $this->assertStringContainsString('enabled', $output);
        $this->assertStringContainsString('development_mode', $output);
        $this->assertStringContainsString('registered_services', $output);
        $this->assertStringContainsString('event_bus_status', $output);
    }

    public function testShowConfig()
    {
        $config = [
            'enabled' => true,
            'development_mode' => true,
            'security' => [
                'require_authentication' => true,
                'allowed_origins' => ['http://localhost'],
            ],
            'features' => [
                'agentic' => true,
                'development' => true,
            ],
        ];

        $this->configManager->method('get')
            ->willReturn($config);

        $exitCode = $this->artisan('mcp:server', [
            'action' => 'config',
            '--format' => 'json'
        ]);

        $this->assertEquals(0, $exitCode);
        $output = Artisan::output();
        
        $this->assertStringContainsString('enabled', $output);
        $this->assertStringContainsString('development_mode', $output);
        $this->assertStringContainsString('security.require_authentication', $output);
    }

    public function testShowFeatures()
    {
        $features = [
            'agentic' => true,
            'development' => true,
            'monitoring' => false,
        ];

        $this->configManager->method('get')
            ->with('features')
            ->willReturn($features);

        $exitCode = $this->artisan('mcp:server', [
            'action' => 'features',
            '--format' => 'json'
        ]);

        $this->assertEquals(0, $exitCode);
        $output = Artisan::output();
        
        $this->assertStringContainsString('agentic', $output);
        $this->assertStringContainsString('development', $output);
        $this->assertStringContainsString('monitoring', $output);
    }

    public function testShowServices()
    {
        $services = [
            'service1' => new \stdClass(),
            'service2' => new \stdClass(),
        ];

        $this->server->method('getServices')
            ->willReturn($services);

        $exitCode = $this->artisan('mcp:server', [
            'action' => 'services',
            '--format' => 'json'
        ]);

        $this->assertEquals(0, $exitCode);
        $output = Artisan::output();
        
        $this->assertStringContainsString('service1', $output);
        $this->assertStringContainsString('service2', $output);
        $this->assertStringContainsString('Active', $output);
    }

    public function testUnknownAction()
    {
        $exitCode = $this->artisan('mcp:server', [
            'action' => 'unknown-action'
        ]);

        $this->assertEquals(1, $exitCode);
        $this->assertStringContainsString('Unknown action', Artisan::output());
    }

    public function testServerDisabled()
    {
        $server = $this->createMock(Server::class);
        $server->method('isEnabled')->willReturn(false);
        $this->app->instance(Server::class, $server);

        $exitCode = $this->artisan('mcp:server', [
            'action' => 'status'
        ]);

        $this->assertEquals(1, $exitCode);
        $this->assertStringContainsString('not enabled', Artisan::output());
    }
} 