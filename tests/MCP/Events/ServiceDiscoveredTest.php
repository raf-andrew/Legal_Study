<?php

namespace Tests\Mcp\Events;

use Mcp\Events\ServiceDiscovered;
use Tests\TestCase;

class ServiceDiscoveredTest extends TestCase
{
    public function testEventConstruction(): void
    {
        $service = [
            'class' => 'App\\Services\\TestService',
            'methods' => ['testMethod'],
            'metadata' => ['type' => 'test']
        ];

        $event = new ServiceDiscovered($service);
        
        $this->assertEquals($service, $event->service);
    }

    public function testEventSerialization(): void
    {
        $service = [
            'class' => 'App\\Services\\TestService',
            'methods' => ['testMethod'],
            'metadata' => ['type' => 'test']
        ];

        $event = new ServiceDiscovered($service);
        $serialized = serialize($event);
        $unserialized = unserialize($serialized);
        
        $this->assertEquals($service, $unserialized->service);
    }

    public function testEventBroadcasting(): void
    {
        $service = [
            'class' => 'App\\Services\\TestService',
            'methods' => ['testMethod'],
            'metadata' => ['type' => 'test']
        ];

        $event = new ServiceDiscovered($service);
        
        $this->assertEquals([], $event->broadcastOn());
    }
} 