<?php

namespace Tests\Mcp\Discovery;

use Mcp\Discovery\Discovery;
use Mcp\Discovery\ServiceRegistry;
use Mcp\Discovery\ServiceHealthMonitor;
use Tests\TestCase;
use Illuminate\Support\Facades\Cache;
use Illuminate\Support\Facades\Log;
use ReflectionClass;
use Illuminate\Support\Facades\Config;
use Mockery;

class DiscoveryTest extends TestCase
{
    /**
     * @var Discovery
     */
    protected $discovery;

    /**
     * @var ServiceRegistry
     */
    protected $registry;

    /**
     * @var ServiceHealthMonitor
     */
    protected $healthMonitor;

    /**
     * Setup the test environment.
     */
    protected function setUp(): void
    {
        parent::setUp();

        $this->discovery = new Discovery();
        $this->registry = new ServiceRegistry();
        $this->healthMonitor = new ServiceHealthMonitor();

        Cache::clear();
        Log::swap(new \Illuminate\Log\LogManager(app()));
    }

    /**
     * Test service discovery
     */
    public function testServiceDiscovery(): void
    {
        Config::set('mcp.discovery.paths', [__DIR__ . '/../../Fixtures/Services']);
        Config::set('mcp.discovery.exclude_paths', []);

        $services = $this->discovery->scanServices();
        
        $this->assertIsArray($services);
        $this->assertNotEmpty($services);
        
        foreach ($services as $service) {
            $this->assertArrayHasKey('class', $service);
            $this->assertArrayHasKey('methods', $service);
            $this->assertArrayHasKey('metadata', $service);
        }
    }

    /**
     * Test service registration
     */
    public function testServiceRegistration(): void
    {
        $service = [
            'class' => 'TestService',
            'methods' => [
                ['name' => 'testMethod', 'parameters' => [], 'returnType' => 'void']
            ],
            'metadata' => [
                'namespace' => 'Test\\Namespace',
                'interfaces' => ['TestInterface']
            ]
        ];

        $this->assertTrue($this->registry->register($service));
        $this->assertFalse($this->registry->register([])); // Invalid service
    }

    /**
     * Test service lookup
     */
    public function testServiceLookup(): void
    {
        $service = [
            'class' => 'TestService',
            'methods' => [
                ['name' => 'testMethod', 'parameters' => [], 'returnType' => 'void']
            ],
            'metadata' => [
                'namespace' => 'Test\\Namespace',
                'interfaces' => ['TestInterface']
            ]
        ];

        $this->registry->register($service);

        $foundService = $this->registry->find('TestService');
        $this->assertEquals($service, $foundService);

        $notFoundService = $this->registry->find('NonExistentService');
        $this->assertNull($notFoundService);
    }

    /**
     * Test service health monitoring
     */
    public function testServiceHealthMonitoring(): void
    {
        $startTime = microtime(true);
        $endTime = $startTime + 0.1; // 100ms
        $memoryUsage = 1024 * 1024; // 1MB

        $this->healthMonitor->recordCall(
            'TestService',
            'testMethod',
            $startTime,
            $endTime,
            true,
            $memoryUsage
        );

        $metrics = $this->healthMonitor->getHealthMetrics('TestService', 'testMethod');
        $this->assertNotNull($metrics);
        $this->assertEquals(1, $metrics['calls']);
        $this->assertEquals(1, $metrics['successes']);
        $this->assertEquals(0, $metrics['errors']);
        $this->assertGreaterThan(0, $metrics['total_response_time']);
        $this->assertEquals($memoryUsage, $metrics['max_memory_usage']);
    }

    /**
     * Test health threshold warnings
     */
    public function testHealthThresholdWarnings(): void
    {
        Log::shouldReceive('warning')
            ->times(3)
            ->with(\Mockery::type('string'));

        // Record calls that exceed thresholds
        for ($i = 0; $i < 10; $i++) {
            $this->healthMonitor->recordCall(
                'TestService',
                'testMethod',
                microtime(true),
                microtime(true) + 2, // 2000ms > 1000ms threshold
                $i < 8, // 20% error rate > 5% threshold
                256 * 1024 * 1024 // 256MB > 128MB threshold
            );
        }
    }

    /**
     * Test cache persistence
     */
    public function testCachePersistence(): void
    {
        $service = [
            'class' => 'TestService',
            'methods' => [
                ['name' => 'testMethod', 'parameters' => [], 'returnType' => 'void']
            ],
            'metadata' => [
                'namespace' => 'Test\\Namespace',
                'interfaces' => ['TestInterface']
            ]
        ];

        $this->registry->register($service);

        // Create new instance to test cache loading
        $newRegistry = new ServiceRegistry();
        $foundService = $newRegistry->find('TestService');
        $this->assertEquals($service, $foundService);
    }

    /**
     * Test service type filtering
     */
    public function testServiceTypeFiltering(): void
    {
        $services = [
            [
                'class' => 'ServiceA',
                'methods' => [],
                'metadata' => ['interfaces' => ['InterfaceA']]
            ],
            [
                'class' => 'ServiceB',
                'methods' => [],
                'metadata' => ['interfaces' => ['InterfaceB']]
            ]
        ];

        $this->registry->registerMany($services);

        $interfaceAServices = $this->registry->findByType('InterfaceA');
        $this->assertCount(1, $interfaceAServices);
        $this->assertEquals('ServiceA', $interfaceAServices->first()['class']);

        $interfaceBServices = $this->registry->findByType('InterfaceB');
        $this->assertCount(1, $interfaceBServices);
        $this->assertEquals('ServiceB', $interfaceBServices->first()['class']);
    }

    /**
     * Test method discovery
     */
    public function testMethodDiscovery(): void
    {
        $reflection = new ReflectionClass($this->discovery);
        $method = $reflection->getMethod('getServiceMethods');
        $method->setAccessible(true);

        $methods = $method->invoke($this->discovery, 'App\\Services\\TestService');
        
        $this->assertIsArray($methods);
        $this->assertNotEmpty($methods);
        $this->assertContains('testMethod', $methods);
    }

    /**
     * Test service unregistration
     */
    public function testServiceUnregistration(): void
    {
        $service = [
            'class' => 'TestService',
            'methods' => [],
            'metadata' => []
        ];

        $this->registry->register($service);
        $this->assertTrue($this->registry->unregister('TestService'));
        $this->assertNull($this->registry->find('TestService'));
        $this->assertFalse($this->registry->unregister('NonExistentService'));
    }

    /**
     * Test metrics clearing
     */
    public function testMetricsClearing(): void
    {
        $this->healthMonitor->recordCall(
            'TestService',
            'testMethod',
            microtime(true),
            microtime(true) + 0.1,
            true,
            1024 * 1024
        );

        $this->healthMonitor->clearMetrics();
        $this->assertEmpty($this->healthMonitor->getAllMetrics());
    }

    public function testServiceTypeDetection(): void
    {
        $reflection = new ReflectionClass($this->discovery);
        $method = $reflection->getMethod('isServiceClass');
        $method->setAccessible(true);

        $this->assertTrue($method->invoke($this->discovery, 'App\\Services\\TestService'));
        $this->assertFalse($method->invoke($this->discovery, 'App\\Models\\TestModel'));
    }

    public function testMetadataCollection(): void
    {
        $reflection = new ReflectionClass($this->discovery);
        $method = $reflection->getMethod('getServiceMetadata');
        $method->setAccessible(true);

        $metadata = $method->invoke($this->discovery, 'App\\Services\\TestService');
        
        $this->assertIsArray($metadata);
        $this->assertArrayHasKey('type', $metadata);
    }

    public function testExcludedPaths(): void
    {
        Config::set('mcp.discovery.exclude_paths', ['vendor', 'tests']);

        $reflection = new ReflectionClass($this->discovery);
        $method = $reflection->getMethod('isExcludedPath');
        $method->setAccessible(true);

        $this->assertTrue($method->invoke($this->discovery, '/path/to/vendor/package'));
        $this->assertTrue($method->invoke($this->discovery, '/path/to/tests/unit'));
        $this->assertFalse($method->invoke($this->discovery, '/path/to/app/Services'));
    }

    public function testServiceFiltering(): void
    {
        $services = [
            [
                'class' => 'App\\Services\\TestService1',
                'methods' => ['testMethod1'],
                'metadata' => ['type' => 'test1']
            ],
            [
                'class' => 'App\\Services\\TestService2',
                'methods' => ['testMethod2'],
                'metadata' => ['type' => 'test2']
            ]
        ];

        $filtered = $this->discovery->filterServices($services, 'test1');
        
        $this->assertCount(1, $filtered);
        $this->assertEquals('App\\Services\\TestService1', $filtered[0]['class']);
    }

    public function testServiceFilteringByMethod(): void
    {
        $services = [
            [
                'class' => 'App\\Services\\TestService1',
                'methods' => ['testMethod1'],
                'metadata' => ['type' => 'test1']
            ],
            [
                'class' => 'App\\Services\\TestService2',
                'methods' => ['testMethod2'],
                'metadata' => ['type' => 'test2']
            ]
        ];

        $filtered = $this->discovery->filterServices($services, null, 'testMethod1');
        
        $this->assertCount(1, $filtered);
        $this->assertEquals('App\\Services\\TestService1', $filtered[0]['class']);
    }

    public function testServiceFilteringByTypeAndMethod(): void
    {
        $services = [
            [
                'class' => 'App\\Services\\TestService1',
                'methods' => ['testMethod1'],
                'metadata' => ['type' => 'test1']
            ],
            [
                'class' => 'App\\Services\\TestService2',
                'methods' => ['testMethod2'],
                'metadata' => ['type' => 'test2']
            ]
        ];

        $filtered = $this->discovery->filterServices($services, 'test1', 'testMethod1');
        
        $this->assertCount(1, $filtered);
        $this->assertEquals('App\\Services\\TestService1', $filtered[0]['class']);
    }
} 