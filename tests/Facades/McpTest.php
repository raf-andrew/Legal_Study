<?php

namespace Tests\Facades;

use App\Facades\Mcp;
use App\Mcp\Core\Server;
use Illuminate\Support\Facades\Config;
use Tests\TestCase;

class McpTest extends TestCase
{
    protected function setUp(): void
    {
        parent::setUp();
        Config::set('app.env', 'local');
        Config::set('mcp.enabled', true);
    }

    public function test_facade_initialization(): void
    {
        $this->assertInstanceOf(Server::class, Mcp::getFacadeRoot());
    }

    public function test_is_enabled(): void
    {
        $this->assertTrue(Mcp::isEnabled());
        
        Config::set('mcp.enabled', false);
        $this->assertFalse(Mcp::isEnabled());
    }

    public function test_is_production(): void
    {
        $this->assertFalse(Mcp::isProduction());
        
        Config::set('app.env', 'production');
        $this->assertTrue(Mcp::isProduction());
    }

    public function test_get_config(): void
    {
        $config = Mcp::getConfig();
        
        $this->assertIsArray($config);
        $this->assertArrayHasKey('enabled', $config);
        $this->assertArrayHasKey('debug', $config);
        $this->assertArrayHasKey('services', $config);
        $this->assertArrayHasKey('security', $config);
        $this->assertArrayHasKey('monitoring', $config);
    }

    public function test_get_health_metrics(): void
    {
        $metrics = Mcp::getHealthMetrics();
        
        $this->assertIsArray($metrics);
        $this->assertArrayHasKey('timestamp', $metrics);
        $this->assertArrayHasKey('cpu_usage', $metrics);
        $this->assertArrayHasKey('memory_usage', $metrics);
        $this->assertArrayHasKey('disk_usage', $metrics);
        $this->assertArrayHasKey('services', $metrics);
    }

    public function test_get_services(): void
    {
        $services = Mcp::getServices();
        
        $this->assertIsArray($services);
        $this->assertEmpty($services);
    }

    public function test_register_service(): void
    {
        $serviceName = 'test_service';
        $serviceConfig = ['enabled' => true];
        
        $this->assertTrue(Mcp::registerService($serviceName, $serviceConfig));
        
        $services = Mcp::getServices();
        $this->assertArrayHasKey($serviceName, $services);
        $this->assertEquals($serviceConfig, $services[$serviceName]['config']);
    }

    public function test_duplicate_service_registration(): void
    {
        $serviceName = 'test_service';
        $serviceConfig = ['enabled' => true];
        
        $this->assertTrue(Mcp::registerService($serviceName, $serviceConfig));
        $this->assertFalse(Mcp::registerService($serviceName, $serviceConfig));
    }
} 