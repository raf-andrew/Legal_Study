<?php

namespace Tests\Unit\Mcp;

use App\Mcp\Server;
use App\Mcp\EventBus;
use App\Mcp\ConfigurationManager;
use App\Mcp\SecurityManager;
use Illuminate\Support\Facades\Config;
use Tests\TestCase;

class ServerTest extends TestCase
{
    protected $server;
    protected $config;

    protected function setUp(): void
    {
        parent::setUp();
        
        Config::set('app.env', 'local');
        Config::set('mcp', [
            'enabled' => true,
            'security' => [
                'require_authentication' => false,
                'allowed_origins' => ['http://localhost'],
                'rate_limit' => 100,
            ],
            'features' => [
                'agentic' => true,
                'development' => true,
                'monitoring' => true,
            ],
        ]);

        $this->server = new Server();
    }

    public function testServerInitialization()
    {
        $this->assertTrue($this->server->isEnabled());
        $this->assertTrue($this->server->isDevelopment());
    }

    public function testServiceRegistration()
    {
        $service = new \stdClass();
        $result = $this->server->registerService($service);
        
        $this->assertTrue($result);
        $this->assertNotNull($this->server->getService(get_class($service)));
    }

    public function testEventBusIntegration()
    {
        $eventBus = $this->server->getEventBus();
        $this->assertInstanceOf(EventBus::class, $eventBus);

        $eventReceived = false;
        $eventBus->subscribe('test.event', function () use (&$eventReceived) {
            $eventReceived = true;
        });

        $eventBus->publish('test.event');
        $this->assertTrue($eventReceived);
    }

    public function testConfigurationManagement()
    {
        $configManager = $this->server->getService(ConfigurationManager::class);
        $this->assertInstanceOf(ConfigurationManager::class, $configManager);

        $this->assertTrue($configManager->isEnabled());
        $this->assertTrue($configManager->isDevelopmentMode());
        $this->assertTrue($configManager->isFeatureEnabled('agentic'));
    }

    public function testSecurityManagement()
    {
        $securityManager = $this->server->getService(SecurityManager::class);
        $this->assertInstanceOf(SecurityManager::class, $securityManager);

        // Test rate limiting
        $this->assertTrue($securityManager->checkRateLimit('test'));
        
        // Test origin validation
        $this->assertTrue($securityManager->validateOrigin('http://localhost'));
        $this->assertFalse($securityManager->validateOrigin('http://invalid-origin.com'));
    }

    public function testServerDisabledInProduction()
    {
        Config::set('app.env', 'production');
        Config::set('mcp.enabled', false);
        
        $server = new Server();
        $this->assertFalse($server->isEnabled());
        
        $service = new \stdClass();
        $result = $server->registerService($service);
        $this->assertFalse($result);
    }

    public function testConfigurationValidation()
    {
        $configManager = $this->server->getService(ConfigurationManager::class);
        $errors = $configManager->validateConfiguration();
        
        $this->assertEmpty($errors);
    }

    public function testEventBusEventHistory()
    {
        $eventBus = $this->server->getEventBus();
        
        $eventBus->publish('test.event', ['data' => 'test']);
        $events = $eventBus->getEvents('test.event');
        
        $this->assertCount(1, $events);
        $this->assertEquals('test', $events[0]['data']['data']);
    }
} 