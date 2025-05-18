<?php

namespace Tests\Feature;

use Tests\TestCase;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Cache;
use Illuminate\Support\Facades\Queue;

class HealthCheckTest extends TestCase
{
    public function test_health_check_returns_200()
    {
        $response = $this->get('/health');

        $this->assertSuccessResponse($response, [
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
        $this->assertPerformance(function () {
            $this->get('/health');
        }, 0.5); // Should respond within 500ms
    }

    public function test_health_check_with_database_failure()
    {
        // Simulate database failure
        DB::shouldReceive('connection->getPdo')
            ->once()
            ->andThrow(new \Exception('Database connection failed'));

        $response = $this->get('/health');

        $this->assertSuccessResponse($response, [
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

        $response = $this->get('/health');

        $this->assertSuccessResponse($response, [
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

        $response = $this->get('/health');

        $this->assertSuccessResponse($response, [
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
        // Make multiple requests in quick succession
        for ($i = 0; $i < 60; $i++) {
            $this->get('/health');
        }

        // The next request should be rate limited
        $response = $this->get('/health');
        $this->assertRateLimited($response);
    }
}
