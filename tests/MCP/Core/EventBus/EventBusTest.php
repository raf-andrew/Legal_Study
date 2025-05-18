<?php

namespace Tests\Mcp\Core\EventBus;

use App\Mcp\Core\EventBus\EventBus;
use App\Mcp\Core\EventBus\EventBusInterface;
use Tests\TestCase;

class EventBusTest extends TestCase
{
    protected EventBusInterface $eventBus;

    protected function setUp(): void
    {
        parent::setUp();
        $this->eventBus = new EventBus();
    }

    public function test_interface_implementation(): void
    {
        $this->assertInstanceOf(EventBusInterface::class, $this->eventBus);
    }

    public function test_handler_registration(): void
    {
        $eventType = 'test.event';
        $handler = function ($data) { return $data; };

        $this->assertTrue($this->eventBus->registerHandler($eventType, $handler));
        $this->assertTrue($this->eventBus->hasHandlers($eventType));
        $this->assertCount(1, $this->eventBus->getHandlers($eventType));
    }

    public function test_duplicate_handler_registration(): void
    {
        $eventType = 'test.event';
        $handler = function ($data) { return $data; };

        $this->assertTrue($this->eventBus->registerHandler($eventType, $handler));
        $this->assertFalse($this->eventBus->registerHandler($eventType, $handler));
        $this->assertCount(1, $this->eventBus->getHandlers($eventType));
    }

    public function test_handler_unregistration(): void
    {
        $eventType = 'test.event';
        $handler = function ($data) { return $data; };

        $this->eventBus->registerHandler($eventType, $handler);
        $this->assertTrue($this->eventBus->unregisterHandler($eventType, $handler));
        $this->assertFalse($this->eventBus->hasHandlers($eventType));
    }

    public function test_nonexistent_handler_unregistration(): void
    {
        $eventType = 'test.event';
        $handler = function ($data) { return $data; };

        $this->assertFalse($this->eventBus->unregisterHandler($eventType, $handler));
    }

    public function test_event_dispatch(): void
    {
        $eventType = 'test.event';
        $eventData = ['test' => 'data'];
        $result = null;

        $handler = function ($data) use (&$result) {
            $result = $data;
            return $data;
        };

        $this->eventBus->registerHandler($eventType, $handler);
        $results = $this->eventBus->dispatch($eventType, $eventData);

        $this->assertEquals($eventData, $result);
        $this->assertCount(1, $results);
        $this->assertEquals($eventData, $results[0]);
    }

    public function test_multiple_handlers(): void
    {
        $eventType = 'test.event';
        $eventData = ['test' => 'data'];
        $results = [];

        $handler1 = function ($data) use (&$results) {
            $results[] = 'handler1';
            return $data;
        };

        $handler2 = function ($data) use (&$results) {
            $results[] = 'handler2';
            return $data;
        };

        $this->eventBus->registerHandler($eventType, $handler1);
        $this->eventBus->registerHandler($eventType, $handler2);
        
        $this->eventBus->dispatch($eventType, $eventData);
        
        $this->assertCount(2, $results);
        $this->assertEquals(['handler1', 'handler2'], $results);
    }

    public function test_handler_priority(): void
    {
        $eventType = 'test.event';
        $eventData = ['test' => 'data'];
        $results = [];

        $handler1 = function ($data) use (&$results) {
            $results[] = 'handler1';
            return $data;
        };

        $handler2 = function ($data) use (&$results) {
            $results[] = 'handler2';
            return $data;
        };

        $this->eventBus->registerHandler($eventType, $handler1, 0);
        $this->eventBus->registerHandler($eventType, $handler2, 1);
        
        $this->eventBus->dispatch($eventType, $eventData);
        
        $this->assertCount(2, $results);
        $this->assertEquals(['handler2', 'handler1'], $results);
    }

    public function test_handler_exception_handling(): void
    {
        $eventType = 'test.event';
        $eventData = ['test' => 'data'];

        $handler = function ($data) {
            throw new \RuntimeException('Test exception');
        };

        $this->eventBus->registerHandler($eventType, $handler);
        $results = $this->eventBus->dispatch($eventType, $eventData);

        $this->assertCount(1, $results);
        $this->assertNull($results[0]);
    }

    public function test_clear_handlers(): void
    {
        $eventType = 'test.event';
        $handler = function ($data) { return $data; };

        $this->eventBus->registerHandler($eventType, $handler);
        $this->assertTrue($this->eventBus->clearHandlers($eventType));
        $this->assertFalse($this->eventBus->hasHandlers($eventType));
    }

    public function test_clear_nonexistent_handlers(): void
    {
        $eventType = 'test.event';
        $this->assertFalse($this->eventBus->clearHandlers($eventType));
    }

    public function test_get_handlers(): void
    {
        $eventType = 'test.event';
        $handler = function ($data) { return $data; };

        $this->eventBus->registerHandler($eventType, $handler);
        $handlers = $this->eventBus->getHandlers($eventType);

        $this->assertCount(1, $handlers);
        $this->assertSame($handler, $handlers[0]);
    }

    public function test_get_nonexistent_handlers(): void
    {
        $eventType = 'test.event';
        $handlers = $this->eventBus->getHandlers($eventType);

        $this->assertIsArray($handlers);
        $this->assertEmpty($handlers);
    }
} 