<?php

namespace Tests\Unit\Mcp\Service;

use App\Mcp\Service\Discovery;
use App\Mcp\ConfigurationManager;
use App\Mcp\EventBus;
use Illuminate\Support\Facades\Event;
use Illuminate\Support\Facades\Route;
use Illuminate\Support\Facades\Config;
use Illuminate\Support\Facades\File;
use Tests\TestCase;

class DiscoveryTest extends TestCase
{
    protected $discovery;
    protected $config;
    protected $eventBus;

    protected function setUp(): void
    {
        parent::setUp();

        $this->config = $this->createMock(ConfigurationManager::class);
        $this->eventBus = $this->createMock(EventBus::class);
        
        $this->config->method('get')
            ->with('services.discovery.interval', 60)
            ->willReturn(60);

        $this->discovery = new Discovery($this->config, $this->eventBus);
    }

    public function testInitialization()
    {
        $this->config->expects($this->once())
            ->method('get')
            ->with('services.discovery.enabled', true)
            ->willReturn(true);

        $this->eventBus->expects($this->once())
            ->method('subscribe')
            ->with('discovery.tick', $this->callback(function ($callback) {
                return is_callable($callback);
            }));

        $discovery = new Discovery($this->config, $this->eventBus);
        $this->assertInstanceOf(Discovery::class, $discovery);
    }

    public function testServiceDiscovery()
    {
        $this->config->method('get')
            ->willReturnCallback(function ($key, $default) {
                switch ($key) {
                    case 'services.discovery.enabled':
                        return true;
                    case 'services.discovery.paths':
                        return [app_path('Services')];
                    default:
                        return $default;
                }
            });

        File::shouldReceive('exists')
            ->with(app_path('Services'))
            ->andReturn(true);

        File::shouldReceive('allFiles')
            ->with(app_path('Services'))
            ->andReturn([
                new \SplFileInfo(app_path('Services/TestService.php')),
            ]);

        File::shouldReceive('get')
            ->with(app_path('Services/TestService.php'))
            ->andReturn('
                <?php
                namespace App\Services;
                class TestService {
                    public function testMethod() {}
                }
            ');

        $this->eventBus->expects($this->atLeastOnce())
            ->method('publish')
            ->with('service.discovered', $this->callback(function ($service) {
                return isset($service['name']) && $service['name'] === 'App\\Services\\TestService';
            }));

        $discovery = new Discovery($this->config, $this->eventBus);
        $services = $discovery->getServices();

        $this->assertCount(1, $services);
        $this->assertEquals('App\\Services\\TestService', $services->first()['name']);
    }

    public function testServiceTypeDetection()
    {
        $this->config->method('get')
            ->willReturnCallback(function ($key, $default) {
                switch ($key) {
                    case 'services.discovery.enabled':
                        return true;
                    case 'services.discovery.paths':
                        return [app_path('Services')];
                    default:
                        return $default;
                }
            });

        File::shouldReceive('exists')
            ->with(app_path('Services'))
            ->andReturn(true);

        File::shouldReceive('allFiles')
            ->with(app_path('Services'))
            ->andReturn([
                new \SplFileInfo(app_path('Services/HttpService.php')),
            ]);

        File::shouldReceive('get')
            ->with(app_path('Services/HttpService.php'))
            ->andReturn('
                <?php
                namespace App\Services;
                use Illuminate\Contracts\Http\Kernel;
                class HttpService implements Kernel {
                    public function handle() {}
                }
            ');

        $discovery = new Discovery($this->config, $this->eventBus);
        $services = $discovery->getServices();

        $this->assertEquals('http_kernel', $services->first()['type']);
    }

    public function testServiceMethodDiscovery()
    {
        $this->config->method('get')
            ->willReturnCallback(function ($key, $default) {
                switch ($key) {
                    case 'services.discovery.enabled':
                        return true;
                    case 'services.discovery.paths':
                        return [app_path('Services')];
                    default:
                        return $default;
                }
            });

        File::shouldReceive('exists')
            ->with(app_path('Services'))
            ->andReturn(true);

        File::shouldReceive('allFiles')
            ->with(app_path('Services'))
            ->andReturn([
                new \SplFileInfo(app_path('Services/MethodService.php')),
            ]);

        File::shouldReceive('get')
            ->with(app_path('Services/MethodService.php'))
            ->andReturn('
                <?php
                namespace App\Services;
                class MethodService {
                    public function publicMethod() {}
                    protected function protectedMethod() {}
                    private function privateMethod() {}
                }
            ');

        $discovery = new Discovery($this->config, $this->eventBus);
        $services = $discovery->getServices();
        $methods = $services->first()['methods'];

        $this->assertContains('publicMethod', $methods);
        $this->assertNotContains('protectedMethod', $methods);
        $this->assertNotContains('privateMethod', $methods);
    }

    public function testServiceMetadata()
    {
        $this->config->method('get')
            ->willReturnCallback(function ($key, $default) {
                switch ($key) {
                    case 'services.discovery.enabled':
                        return true;
                    case 'services.discovery.paths':
                        return [app_path('Services')];
                    default:
                        return $default;
                }
            });

        File::shouldReceive('exists')
            ->with(app_path('Services'))
            ->andReturn(true);

        File::shouldReceive('allFiles')
            ->with(app_path('Services'))
            ->andReturn([
                new \SplFileInfo(app_path('Services/MetadataService.php')),
            ]);

        File::shouldReceive('get')
            ->with(app_path('Services/MetadataService.php'))
            ->andReturn('
                <?php
                namespace App\Services;
                interface TestInterface {}
                trait TestTrait {}
                class MetadataService implements TestInterface {
                    use TestTrait;
                }
            ');

        $discovery = new Discovery($this->config, $this->eventBus);
        $services = $discovery->getServices();
        $metadata = $services->first()['metadata'];

        $this->assertFalse($metadata['is_abstract']);
        $this->assertFalse($metadata['is_final']);
        $this->assertFalse($metadata['is_interface']);
        $this->assertFalse($metadata['is_trait']);
        $this->assertContains('App\\Services\\TestInterface', $metadata['interfaces']);
        $this->assertContains('App\\Services\\TestTrait', $metadata['traits']);
    }

    public function testGetService()
    {
        $this->config->method('get')
            ->willReturnCallback(function ($key, $default) {
                switch ($key) {
                    case 'services.discovery.enabled':
                        return true;
                    case 'services.discovery.paths':
                        return [app_path('Services')];
                    default:
                        return $default;
                }
            });

        File::shouldReceive('exists')
            ->with(app_path('Services'))
            ->andReturn(true);

        File::shouldReceive('allFiles')
            ->with(app_path('Services'))
            ->andReturn([
                new \SplFileInfo(app_path('Services/TestService.php')),
            ]);

        File::shouldReceive('get')
            ->with(app_path('Services/TestService.php'))
            ->andReturn('
                <?php
                namespace App\Services;
                class TestService {}
            ');

        $discovery = new Discovery($this->config, $this->eventBus);
        
        $service = $discovery->getService('App\\Services\\TestService');
        $this->assertNotNull($service);
        $this->assertEquals('App\\Services\\TestService', $service['name']);

        $nonExistentService = $discovery->getService('NonExistentService');
        $this->assertNull($nonExistentService);
    }

    public function testGetServicesByType()
    {
        $this->config->method('get')
            ->willReturnCallback(function ($key, $default) {
                switch ($key) {
                    case 'services.discovery.enabled':
                        return true;
                    case 'services.discovery.paths':
                        return [app_path('Services')];
                    default:
                        return $default;
                }
            });

        File::shouldReceive('exists')
            ->with(app_path('Services'))
            ->andReturn(true);

        File::shouldReceive('allFiles')
            ->with(app_path('Services'))
            ->andReturn([
                new \SplFileInfo(app_path('Services/HttpService.php')),
                new \SplFileInfo(app_path('Services/QueueService.php')),
            ]);

        File::shouldReceive('get')
            ->with(app_path('Services/HttpService.php'))
            ->andReturn('
                <?php
                namespace App\Services;
                use Illuminate\Contracts\Http\Kernel;
                class HttpService implements Kernel {}
            ');

        File::shouldReceive('get')
            ->with(app_path('Services/QueueService.php'))
            ->andReturn('
                <?php
                namespace App\Services;
                use Illuminate\Contracts\Queue\Queue;
                class QueueService implements Queue {}
            ');

        $discovery = new Discovery($this->config, $this->eventBus);
        
        $httpServices = $discovery->getServicesByType('http_kernel');
        $this->assertCount(1, $httpServices);
        $this->assertEquals('App\\Services\\HttpService', $httpServices->first()['name']);

        $queueServices = $discovery->getServicesByType('queue');
        $this->assertCount(1, $queueServices);
        $this->assertEquals('App\\Services\\QueueService', $queueServices->first()['name']);
    }

    public function testDiscoverApiEndpoints()
    {
        // Create test routes
        Route::get('/test', function () {})->name('test.route');
        Route::post('/api/data', function () {})->name('api.data');

        $services = $this->discovery->scan();
        $apiEndpoints = collect($services)->where('type', 'api_endpoint');

        $this->assertNotEmpty($apiEndpoints);
        $this->assertTrue($apiEndpoints->contains('name', 'test'));
        $this->assertTrue($apiEndpoints->contains('name', 'api/data'));
    }

    public function testDiscoverEventListeners()
    {
        // Create test event and listener
        Event::listen('test.event', function () {});

        $services = $this->discovery->scan();
        $eventListeners = collect($services)->where('type', 'event_listener');

        $this->assertNotEmpty($eventListeners);
        $this->assertTrue($eventListeners->contains(function ($service) {
            return $service['metadata']['event'] === 'test.event';
        }));
    }

    public function testServiceFiltering()
    {
        // Create test services
        Route::get('/test', function () {});
        Event::listen('test.event', function () {});

        $services = $this->discovery->scan();

        $apiEndpoints = $this->discovery->getServices('api_endpoint');
        $this->assertNotEmpty($apiEndpoints);
        $this->assertTrue($apiEndpoints->every(function ($service) {
            return $service['type'] === 'api_endpoint';
        }));

        $eventListeners = $this->discovery->getServices('event_listener');
        $this->assertNotEmpty($eventListeners);
        $this->assertTrue($eventListeners->every(function ($service) {
            return $service['type'] === 'event_listener';
        }));
    }

    public function testServiceLookup()
    {
        Route::get('/test', function () {});
        $this->discovery->scan();

        $service = $this->discovery->getService('test');
        $this->assertNotNull($service);
        $this->assertEquals('api_endpoint', $service['type']);
    }

    public function testServiceChanges()
    {
        // Initial scan
        Route::get('/test', function () {});
        $this->discovery->scan();

        // Add new route
        Route::post('/api/data', function () {});

        $this->eventBus->expects($this->once())
            ->method('publish')
            ->with(
                $this->equalTo('service.discovered'),
                $this->callback(function ($data) {
                    return collect($data['services'])->contains('name', 'api/data');
                })
            );

        $this->discovery->scan();
    }

    public function testScanInterval()
    {
        $this->config = $this->createMock(ConfigurationManager::class);
        $this->config->method('get')
            ->with('services.discovery.interval', 60)
            ->willReturn(3600); // 1 hour

        $discovery = new Discovery($this->config, $this->eventBus);

        // First scan should always happen
        $this->assertNotEmpty($discovery->scan());

        // Second scan within interval should return cached results
        $this->assertEquals($discovery->scan(), $discovery->scan());
    }
} 