<?php

namespace Tests\Mcp\Core;

use App\Mcp\Core\Server;
use Illuminate\Support\Facades\Config;
use Illuminate\Support\Facades\Cache;
use Tests\TestCase;

class ServerTest extends TestCase
{
    protected Server $server;

    protected function setUp(): void
    {
        parent::setUp();
        $this->server = new Server();
    }

    public function test_server_initialization(): void
    {
        $this->assertInstanceOf(Server::class, $this->server);
    }

    public function test_production_environment_detection(): void
    {
        Config::set('app.env', 'production');
        $server = new Server();
        $this->assertTrue($server->isProduction());

        Config::set('app.env', 'local');
        $server = new Server();
        $this->assertFalse($server->isProduction());
    }

    public function test_enabled_status(): void
    {
        Config::set('app.env', 'production');
        Config::set('mcp.enabled', false);
        $server = new Server();
        $this->assertFalse($server->isEnabled());

        Config::set('mcp.enabled', true);
        $server = new Server();
        $this->assertTrue($server->isEnabled());

        Config::set('app.env', 'local');
        $server = new Server();
        $this->assertTrue($server->isEnabled());
    }

    public function test_configuration_loading(): void
    {
        $config = [
            'enabled' => true,
            'debug' => true,
            'services' => [
                'test_service' => [
                    'enabled' => true,
                ],
            ],
        ];

        Config::set('mcp', $config);
        $server = new Server();
        $this->assertEquals($config, $server->getConfig());
    }

    public function test_default_configuration(): void
    {
        Config::set('mcp', []);
        $server = new Server();
        $config = $server->getConfig();

        $this->assertIsArray($config);
        $this->assertArrayHasKey('enabled', $config);
        $this->assertArrayHasKey('debug', $config);
        $this->assertArrayHasKey('services', $config);
        $this->assertArrayHasKey('security', $config);
        $this->assertArrayHasKey('monitoring', $config);
    }

    public function test_service_registration(): void
    {
        $serviceName = 'test_service';
        $serviceConfig = ['enabled' => true];

        $this->assertTrue($this->server->registerService($serviceName, $serviceConfig));
        $services = $this->server->getServices();
        
        $this->assertArrayHasKey($serviceName, $services);
        $this->assertEquals($serviceConfig, $services[$serviceName]['config']);
        $this->assertEquals('initializing', $services[$serviceName]['status']);
    }

    public function test_duplicate_service_registration(): void
    {
        $serviceName = 'test_service';
        $serviceConfig = ['enabled' => true];

        $this->assertTrue($this->server->registerService($serviceName, $serviceConfig));
        $this->assertFalse($this->server->registerService($serviceName, $serviceConfig));
    }

    public function test_health_metrics(): void
    {
        $metrics = $this->server->getHealthMetrics();
        
        $this->assertIsArray($metrics);
        $this->assertArrayHasKey('timestamp', $metrics);
        $this->assertArrayHasKey('cpu_usage', $metrics);
        $this->assertArrayHasKey('memory_usage', $metrics);
        $this->assertArrayHasKey('disk_usage', $metrics);
        $this->assertArrayHasKey('services', $metrics);

        $this->assertIsFloat($metrics['cpu_usage']);
        $this->assertIsArray($metrics['memory_usage']);
        $this->assertIsArray($metrics['disk_usage']);
        $this->assertIsArray($metrics['services']);
    }

    public function test_memory_usage_metrics(): void
    {
        $metrics = $this->server->getHealthMetrics();
        $memoryUsage = $metrics['memory_usage'];

        $this->assertArrayHasKey('total', $memoryUsage);
        $this->assertArrayHasKey('peak', $memoryUsage);
        $this->assertIsInt($memoryUsage['total']);
        $this->assertIsInt($memoryUsage['peak']);
        $this->assertGreaterThan(0, $memoryUsage['total']);
        $this->assertGreaterThan(0, $memoryUsage['peak']);
    }

    public function test_disk_usage_metrics(): void
    {
        $metrics = $this->server->getHealthMetrics();
        $diskUsage = $metrics['disk_usage'];

        $this->assertArrayHasKey('total', $diskUsage);
        $this->assertArrayHasKey('free', $diskUsage);
        $this->assertArrayHasKey('used', $diskUsage);
        $this->assertArrayHasKey('percentage', $diskUsage);
        
        $this->assertIsInt($diskUsage['total']);
        $this->assertIsInt($diskUsage['free']);
        $this->assertIsInt($diskUsage['used']);
        $this->assertIsFloat($diskUsage['percentage']);
        
        $this->assertGreaterThan(0, $diskUsage['total']);
        $this->assertGreaterThanOrEqual(0, $diskUsage['free']);
        $this->assertGreaterThanOrEqual(0, $diskUsage['used']);
        $this->assertGreaterThanOrEqual(0, $diskUsage['percentage']);
        $this->assertLessThanOrEqual(100, $diskUsage['percentage']);
    }

    public function test_service_statuses(): void
    {
        $serviceName = 'test_service';
        $serviceConfig = ['enabled' => true];
        
        $this->server->registerService($serviceName, $serviceConfig);
        $metrics = $this->server->getHealthMetrics();
        $services = $metrics['services'];

        $this->assertArrayHasKey($serviceName, $services);
        $this->assertEquals('initializing', $services[$serviceName]['status']);
        $this->assertArrayHasKey('last_check', $services[$serviceName]);
        $this->assertArrayHasKey('metrics', $services[$serviceName]);
    }

    public function test_health_check_caching(): void
    {
        $cacheKey = 'mcp_health_check';
        $this->assertFalse(Cache::has($cacheKey));

        $server = new Server();
        $this->assertTrue(Cache::has($cacheKey));
    }
} 