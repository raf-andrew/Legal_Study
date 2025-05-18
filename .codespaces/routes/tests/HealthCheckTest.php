<?php

namespace Tests\Feature;

use Tests\TestCase;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Cache;
use Illuminate\Support\Facades\Redis;

class HealthCheckTest extends TestCase
{
    use RefreshDatabase;

    /** @test */
    public function health_check_returns_200_when_all_services_are_healthy()
    {
        $response = $this->getJson('/api/health');

        $response->assertStatus(200)
            ->assertJsonStructure([
                'status',
                'services' => [
                    'database',
                    'cache',
                    'redis',
                    'storage'
                ],
                'timestamp'
            ])
            ->assertJson([
                'status' => 'healthy',
                'services' => [
                    'database' => 'up',
                    'cache' => 'up',
                    'redis' => 'up',
                    'storage' => 'up'
                ]
            ]);
    }

    /** @test */
    public function health_check_returns_503_when_database_is_down()
    {
        // Simulate database connection error
        $this->mock(\Illuminate\Database\Connection::class)
            ->shouldReceive('getPdo')
            ->andThrow(new \Exception('Database connection error'));

        $response = $this->getJson('/api/health');

        $response->assertStatus(503)
            ->assertJson([
                'status' => 'unhealthy',
                'services' => [
                    'database' => 'down'
                ]
            ]);
    }

    /** @test */
    public function health_check_returns_503_when_cache_is_down()
    {
        // Simulate cache connection error
        $this->mock(\Illuminate\Cache\CacheManager::class)
            ->shouldReceive('store')
            ->andThrow(new \Exception('Cache connection error'));

        $response = $this->getJson('/api/health');

        $response->assertStatus(503)
            ->assertJson([
                'status' => 'unhealthy',
                'services' => [
                    'cache' => 'down'
                ]
            ]);
    }

    /** @test */
    public function health_check_returns_503_when_redis_is_down()
    {
        // Simulate Redis connection error
        $this->mock(\Illuminate\Redis\RedisManager::class)
            ->shouldReceive('connection')
            ->andThrow(new \Exception('Redis connection error'));

        $response = $this->getJson('/api/health');

        $response->assertStatus(503)
            ->assertJson([
                'status' => 'unhealthy',
                'services' => [
                    'redis' => 'down'
                ]
            ]);
    }

    /** @test */
    public function health_check_returns_503_when_storage_is_down()
    {
        // Simulate storage connection error
        $this->mock(\Illuminate\Filesystem\FilesystemManager::class)
            ->shouldReceive('disk')
            ->andThrow(new \Exception('Storage connection error'));

        $response = $this->getJson('/api/health');

        $response->assertStatus(503)
            ->assertJson([
                'status' => 'unhealthy',
                'services' => [
                    'storage' => 'down'
                ]
            ]);
    }

    /** @test */
    public function health_check_includes_database_metrics()
    {
        $response = $this->getJson('/api/health');

        $response->assertStatus(200)
            ->assertJsonStructure([
                'metrics' => [
                    'database' => [
                        'connections',
                        'query_time'
                    ]
                ]
            ]);
    }

    /** @test */
    public function health_check_includes_cache_metrics()
    {
        $response = $this->getJson('/api/health');

        $response->assertStatus(200)
            ->assertJsonStructure([
                'metrics' => [
                    'cache' => [
                        'hits',
                        'misses',
                        'memory_usage'
                    ]
                ]
            ]);
    }

    /** @test */
    public function health_check_includes_redis_metrics()
    {
        $response = $this->getJson('/api/health');

        $response->assertStatus(200)
            ->assertJsonStructure([
                'metrics' => [
                    'redis' => [
                        'connected_clients',
                        'used_memory',
                        'total_connections'
                    ]
                ]
            ]);
    }

    /** @test */
    public function health_check_includes_storage_metrics()
    {
        $response = $this->getJson('/api/health');

        $response->assertStatus(200)
            ->assertJsonStructure([
                'metrics' => [
                    'storage' => [
                        'total_space',
                        'free_space',
                        'used_space'
                    ]
                ]
            ]);
    }

    /** @test */
    public function health_check_performance_is_within_limits()
    {
        $start = microtime(true);

        $response = $this->getJson('/api/health');

        $duration = microtime(true) - $start;

        $response->assertStatus(200);
        $this->assertLessThan(0.5, $duration, 'Health check response time exceeded 0.5 seconds');
    }

    /** @test */
    public function health_check_is_rate_limited()
    {
        for ($i = 0; $i < 60; $i++) {
            $response = $this->getJson('/api/health');
        }

        $response = $this->getJson('/api/health');

        $response->assertStatus(429)
            ->assertJson([
                'message' => 'Too many requests'
            ]);
    }

    /** @test */
    public function health_check_handles_concurrent_requests()
    {
        $promises = [];
        for ($i = 0; $i < 10; $i++) {
            $promises[] = $this->getJson('/api/health');
        }

        foreach ($promises as $response) {
            $response->assertStatus(200);
        }
    }

    /** @test */
    public function health_check_includes_version_information()
    {
        $response = $this->getJson('/api/health');

        $response->assertStatus(200)
            ->assertJsonStructure([
                'version' => [
                    'app',
                    'php',
                    'database',
                    'cache',
                    'redis'
                ]
            ]);
    }

    /** @test */
    public function health_check_includes_environment_information()
    {
        $response = $this->getJson('/api/health');

        $response->assertStatus(200)
            ->assertJsonStructure([
                'environment' => [
                    'name',
                    'debug',
                    'timezone'
                ]
            ]);
    }
}
