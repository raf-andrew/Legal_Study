<?php

namespace Tests\Unit\Mcp;

use App\Mcp\EventBus;
use Tests\TestCase;

class EventBusTest extends TestCase
{
    protected $eventBus;

    protected function setUp(): void
    {
        parent::setUp();
        $this->eventBus = new EventBus();
    }

    public function testSubscribe()
    {
        $called = false;
        $callback = function () use (&$called) {
            $called = true;
        };

        $this->eventBus->subscribe('test.event', $callback);
        $this->eventBus->publish('test.event');

        $this->assertTrue($called);
    }

    public function testUnsubscribe()
    {
        $called = false;
        $callback = function () use (&$called) {
            $called = true;
        };

        $this->eventBus->subscribe('test.event', $callback);
        $this->eventBus->unsubscribe('test.event', $callback);
        $this->eventBus->publish('test.event');

        $this->assertFalse($called);
    }

    public function testPublishWithData()
    {
        $receivedData = null;
        $callback = function ($data) use (&$receivedData) {
            $receivedData = $data;
        };

        $testData = ['key' => 'value'];
        $this->eventBus->subscribe('test.event', $callback);
        $this->eventBus->publish('test.event', $testData);

        $this->assertEquals($testData, $receivedData);
    }

    public function testGetEvents()
    {
        $testData = ['key' => 'value'];
        $this->eventBus->publish('test.event', $testData);

        $events = $this->eventBus->getEvents('test.event');
        $this->assertCount(1, $events);
        $this->assertEquals('test.event', $events[0]['event']);
        $this->assertEquals($testData, $events[0]['data']);
    }

    public function testClearEvents()
    {
        $this->eventBus->publish('test.event');
        $this->eventBus->clearEvents();

        $events = $this->eventBus->getEvents();
        $this->assertEmpty($events);
    }

    public function testGetSubscribers()
    {
        $callback = function () {};
        $this->eventBus->subscribe('test.event', $callback);

        $subscribers = $this->eventBus->getSubscribers('test.event');
        $this->assertCount(1, $subscribers);
        $this->assertSame($callback, $subscribers->first());
    }

    public function testMultipleSubscribers()
    {
        $called1 = false;
        $called2 = false;

        $callback1 = function () use (&$called1) {
            $called1 = true;
        };

        $callback2 = function () use (&$called2) {
            $called2 = true;
        };

        $this->eventBus->subscribe('test.event', $callback1);
        $this->eventBus->subscribe('test.event', $callback2);
        $this->eventBus->publish('test.event');

        $this->assertTrue($called1);
        $this->assertTrue($called2);
    }

    public function testSubscriberError()
    {
        $errorCallback = function () {
            throw new \Exception('Test error');
        };

        $called = false;
        $successCallback = function () use (&$called) {
            $called = true;
        };

        $this->eventBus->subscribe('test.event', $errorCallback);
        $this->eventBus->subscribe('test.event', $successCallback);
        $this->eventBus->publish('test.event');

        $this->assertTrue($called);
    }

    public function testPublishNonExistentEvent()
    {
        $this->eventBus->publish('non.existent.event');
        $events = $this->eventBus->getEvents('non.existent.event');
        $this->assertEmpty($events);
    }

    public function testUnsubscribeNonExistentEvent()
    {
        $callback = function () {};
        $this->eventBus->unsubscribe('non.existent.event', $callback);
        $subscribers = $this->eventBus->getSubscribers('non.existent.event');
        $this->assertCount(0, $subscribers);
    }
} 