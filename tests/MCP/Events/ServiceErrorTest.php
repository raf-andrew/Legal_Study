<?php

namespace Tests\Mcp\Events;

use Mcp\Events\ServiceError;
use Tests\TestCase;

class ServiceErrorTest extends TestCase
{
    public function testEventConstruction(): void
    {
        $serviceClass = 'App\\Services\\TestService';
        $method = 'testMethod';
        $error = new \Exception('Test error');

        $event = new ServiceError($serviceClass, $method, $error);
        
        $this->assertEquals($serviceClass, $event->serviceClass);
        $this->assertEquals($method, $event->method);
        $this->assertEquals($error, $event->error);
    }

    public function testEventSerialization(): void
    {
        $serviceClass = 'App\\Services\\TestService';
        $method = 'testMethod';
        $error = new \Exception('Test error');

        $event = new ServiceError($serviceClass, $method, $error);
        $serialized = serialize($event);
        $unserialized = unserialize($serialized);
        
        $this->assertEquals($serviceClass, $unserialized->serviceClass);
        $this->assertEquals($method, $unserialized->method);
        $this->assertEquals($error->getMessage(), $unserialized->error->getMessage());
    }

    public function testEventBroadcasting(): void
    {
        $serviceClass = 'App\\Services\\TestService';
        $method = 'testMethod';
        $error = new \Exception('Test error');

        $event = new ServiceError($serviceClass, $method, $error);
        
        $this->assertEquals([], $event->broadcastOn());
    }
} 