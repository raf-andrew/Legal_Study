<?php

namespace Tests\Mcp\Discovery;

use Mcp\Discovery\ServiceRegistry;
use Tests\TestCase;
use Illuminate\Support\Facades\Cache;
use Mockery;

class ServiceRegistryTest extends TestCase
{
    private ServiceRegistry $registry;

    protected function setUp(): void
    {
        parent::setUp();
        $this->registry = new ServiceRegistry();
    }

    public function testServiceRegistration(): void
    {
        $service = [
            'class' => 'App\\Services\\TestService',
            'methods' => ['testMethod'],
            'metadata' => ['type' => 'test']
        ];

        $this->registry->register($service);
        
        $this->assertEquals($service, $this->registry->find('App\\Services\\TestService'));
    }

    public function testServiceLookup(): void
    {
        $service = [
            'class' => 'App\\Services\\TestService',
            'methods' => ['testMethod'],
            'metadata' => ['type' => 'test']
        ];

        $this->registry->register($service);
        
        $this->assertEquals($service, $this->registry->find('App\\Services\\TestService'));
        $this->assertNull($this->registry->find('App\\Services\\NonExistentService'));
    }

    public function testServiceUnregistration(): void
    {
        $service = [
            'class' => 'App\\Services\\TestService',
            'methods' => ['testMethod'],
            'metadata' => ['type' => 'test']
        ];

        $this->registry->register($service);
        $this->registry->unregister('App\\Services\\TestService');
        
        $this->assertNull($this->registry->find('App\\Services\\TestService'));
    }

    public function testServiceTypeFiltering(): void
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

        foreach ($services as $service) {
            $this->registry->register($service);
        }

        $filtered = $this->registry->getServices('test1');
        
        $this->assertCount(1, $filtered);
        $this->assertEquals('App\\Services\\TestService1', $filtered[0]['class']);
    }

    public function testCachePersistence(): void
    {
        $service = [
            'class' => 'App\\Services\\TestService',
            'methods' => ['testMethod'],
            'metadata' => ['type' => 'test']
        ];

        $this->registry->register($service);
        
        $newRegistry = new ServiceRegistry();
        $this->assertEquals($service, $newRegistry->find('App\\Services\\TestService'));
    }

    public function testCacheTTL(): void
    {
        $service = [
            'class' => 'App\\Services\\TestService',
            'methods' => ['testMethod'],
            'metadata' => ['type' => 'test']
        ];

        $this->registry->register($service);
        
        Cache::shouldReceive('get')
            ->once()
            ->with('mcp.services')
            ->andReturn(null);

        $newRegistry = new ServiceRegistry();
        $this->assertNull($newRegistry->find('App\\Services\\TestService'));
    }

    public function testServiceClear(): void
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

        foreach ($services as $service) {
            $this->registry->register($service);
        }

        $this->registry->clear();
        
        $this->assertEmpty($this->registry->getServices());
    }
} 