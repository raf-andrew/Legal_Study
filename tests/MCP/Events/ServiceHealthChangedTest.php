<?php

namespace Tests\Mcp\Events;

use Mcp\Events\ServiceHealthChanged;
use Tests\TestCase;

class ServiceHealthChangedTest extends TestCase
{
    public function testEventConstruction(): void
    {
        $serviceClass = 'App\\Services\\TestService';
        $method = 'testMethod';
        $metrics = [
            'calls' => 10,
            'successes' => 10,
            'errors' => 0,
            'response_time' => 100,
            'memory_usage' => 1024
        ];

        $event = new ServiceHealthChanged($serviceClass, $method, $metrics);
        
        $this->assertEquals($serviceClass, $event->serviceClass);
        $this->assertEquals($method, $event->method);
        $this->assertEquals($metrics, $event->metrics);
    }

    public function testEventSerialization(): void
    {
        $serviceClass = 'App\\Services\\TestService';
        $method = 'testMethod';
        $metrics = [
            'calls' => 10,
            'successes' => 10,
            'errors' => 0,
            'response_time' => 100,
            'memory_usage' => 1024
        ];

        $event = new ServiceHealthChanged($serviceClass, $method, $metrics);
        $serialized = serialize($event);
        $unserialized = unserialize($serialized);
        
        $this->assertEquals($serviceClass, $unserialized->serviceClass);
        $this->assertEquals($method, $unserialized->method);
        $this->assertEquals($metrics, $unserialized->metrics);
    }

    public function testEventBroadcasting(): void
    {
        $serviceClass = 'App\\Services\\TestService';
        $method = 'testMethod';
        $metrics = [
            'calls' => 10,
            'successes' => 10,
            'errors' => 0,
            'response_time' => 100,
            'memory_usage' => 1024
        ];

        $event = new ServiceHealthChanged($serviceClass, $method, $metrics);
        
        $this->assertEquals([], $event->broadcastOn());
    }
} 