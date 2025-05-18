<?php

namespace Tests\Unit\Mcp\Service;

use App\Mcp\ConfigurationManager;
use App\Mcp\EventBus;
use App\Mcp\Service\Actuator;
use App\Mcp\Service\Discovery;
use Illuminate\Support\Facades\Event;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Route;
use Tests\TestCase;

class ActuatorTest extends TestCase
{
    protected $config;
    protected $eventBus;
    protected $discovery;
    protected $actuator;

    protected function setUp(): void
    {
        parent::setUp();

        $this->config = $this->createMock(ConfigurationManager::class);
        $this->eventBus = $this->createMock(EventBus::class);
        $this->discovery = $this->createMock(Discovery::class);
        
        $this->actuator = new Actuator($this->config, $this->eventBus, $this->discovery);
    }

    public function testExecuteApiAction()
    {
        $service = [
            'type' => 'api_endpoint',
            'name' => 'api/test',
            'metadata' => [
                'methods' => ['GET', 'POST'],
            ],
        ];

        $this->discovery->method('getService')
            ->with('api/test')
            ->willReturn($service);

        Http::fake([
            'api/test' => Http::response(['data' => 'test'], 200),
        ]);

        $result = $this->actuator->executeAction('api/test', 'get');
        $this->assertEquals(['data' => 'test'], $result);

        Http::assertSent(function ($request) {
            return $request->hasHeader('X-MCP-Action', 'true');
        });
    }

    public function testExecuteApiActionUnsupportedMethod()
    {
        $service = [
            'type' => 'api_endpoint',
            'name' => 'api/test',
            'metadata' => [
                'methods' => ['GET'],
            ],
        ];

        $this->discovery->method('getService')
            ->with('api/test')
            ->willReturn($service);

        $this->expectException(\Exception::class);
        $this->expectExceptionMessage('Method POST not supported for endpoint api/test');

        $this->actuator->executeAction('api/test', 'post');
    }

    public function testExecuteServiceAction()
    {
        $testService = new class {
            public function testMethod($param) {
                return "Result: {$param}";
            }
        };

        $service = [
            'type' => 'service_provider',
            'name' => get_class($testService),
        ];

        $this->discovery->method('getService')
            ->with('test_service')
            ->willReturn($service);

        $this->app->instance($service['name'], $testService);

        $result = $this->actuator->executeAction('test_service', 'testMethod', ['param' => 'test']);
        $this->assertEquals('Result: test', $result);
    }

    public function testExecuteServiceActionUnsupportedMethod()
    {
        $testService = new class {};

        $service = [
            'type' => 'service_provider',
            'name' => get_class($testService),
        ];

        $this->discovery->method('getService')
            ->with('test_service')
            ->willReturn($service);

        $this->app->instance($service['name'], $testService);

        $this->expectException(\Exception::class);
        $this->expectExceptionMessage('Action testMethod not supported');

        $this->actuator->executeAction('test_service', 'testMethod');
    }

    public function testExecuteEventAction()
    {
        $eventReceived = false;
        Event::listen('test.event', function ($data) use (&$eventReceived) {
            $eventReceived = $data['test'];
        });

        $service = [
            'type' => 'event_listener',
            'name' => 'TestListener',
            'metadata' => [
                'event' => 'test.event',
            ],
        ];

        $this->discovery->method('getService')
            ->with('test_listener')
            ->willReturn($service);

        $this->actuator->executeAction('test_listener', 'trigger', ['test' => true]);
        $this->assertTrue($eventReceived);
    }

    public function testExecuteEventActionUnsupportedAction()
    {
        $service = [
            'type' => 'event_listener',
            'name' => 'TestListener',
            'metadata' => [
                'event' => 'test.event',
            ],
        ];

        $this->discovery->method('getService')
            ->with('test_listener')
            ->willReturn($service);

        $this->expectException(\Exception::class);
        $this->expectExceptionMessage("Only 'trigger' action is supported for event listeners");

        $this->actuator->executeAction('test_listener', 'unsupported');
    }

    public function testGetAvailableActions()
    {
        $service = [
            'type' => 'api_endpoint',
            'name' => 'api/test',
            'metadata' => [
                'methods' => ['GET', 'POST'],
            ],
        ];

        $this->discovery->method('getService')
            ->with('api/test')
            ->willReturn($service);

        $actions = $this->actuator->getAvailableActions('api/test');
        $this->assertEquals(['GET', 'POST'], $actions);
    }

    public function testServiceNotFound()
    {
        $this->discovery->method('getService')
            ->with('nonexistent')
            ->willReturn(null);

        $this->expectException(\Exception::class);
        $this->expectExceptionMessage('Service not found: nonexistent');

        $this->actuator->executeAction('nonexistent', 'action');
    }

    public function testUnsupportedServiceType()
    {
        $service = [
            'type' => 'unsupported',
            'name' => 'test',
        ];

        $this->discovery->method('getService')
            ->with('test')
            ->willReturn($service);

        $this->expectException(\Exception::class);
        $this->expectExceptionMessage('Unsupported service type: unsupported');

        $this->actuator->executeAction('test', 'action');
    }
} 