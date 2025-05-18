<?php

namespace Tests\Feature;

use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Cache;
use Illuminate\Support\Facades\Queue;

class HealthCheckRouteTest extends RouteTestCase
{
    protected $route = 'health';
    protected $method = 'GET';
    protected $requiresAuth = false;

    public function test_health_check_route_exists()
    {
        $this->assertRouteExists();
    }

    public function test_health_check_returns_200()
    {
        $this->assertRouteResponse(200, [
            'status' => 'healthy',
            'services' => [
                'database' => true,
                'cache' => true,
                'queue' => true
            ]
        ]);
    }

    public function test_health_check_performance()
    {
        $this->assertRoutePerformance();
    }

    public function test_health_check_with_database_failure()
    {
        // Simulate database failure
        DB::shouldReceive('connection->getPdo')
            ->once()
            ->andThrow(new \Exception('Database connection failed'));

        $this->assertRouteResponse(200, [
            'status' => 'unhealthy',
            'services' => [
                'database' => false,
                'cache' => true,
                'queue' => true
            ]
        ]);
    }

    public function test_health_check_with_cache_failure()
    {
        // Simulate cache failure
        Cache::shouldReceive('get')
            ->once()
            ->andThrow(new \Exception('Cache connection failed'));

        $this->assertRouteResponse(200, [
            'status' => 'unhealthy',
            'services' => [
                'database' => true,
                'cache' => false,
                'queue' => true
            ]
        ]);
    }

    public function test_health_check_with_queue_failure()
    {
        // Simulate queue failure
        Queue::shouldReceive('size')
            ->once()
            ->andThrow(new \Exception('Queue connection failed'));

        $this->assertRouteResponse(200, [
            'status' => 'unhealthy',
            'services' => [
                'database' => true,
                'cache' => true,
                'queue' => false
            ]
        ]);
    }

    public function test_health_check_rate_limiting()
    {
        $this->assertRouteRateLimited();
    }
}
