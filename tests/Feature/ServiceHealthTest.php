<?php

namespace Tests\Feature;

use Tests\TestCase;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Redis;
use Illuminate\Support\Facades\Cache;
use Illuminate\Support\Facades\Http;

class ServiceHealthTest extends TestCase
{
    public function test_database_connection()
    {
        try {
            $pdo = DB::connection()->getPdo();
            $this->assertTrue(true, 'Database connection successful');
        } catch (\Exception $e) {
            $this->fail('Database connection failed: ' . $e->getMessage());
        }
    }

    public function test_redis_connection()
    {
        try {
            $ping = Redis::ping();
            $this->assertTrue(true, 'Redis connection successful');
        } catch (\Exception $e) {
            $this->fail('Redis connection failed: ' . $e->getMessage());
        }
    }

    public function test_cache_connection()
    {
        try {
            Cache::put('test_key', 'test_value', 60);
            $value = Cache::get('test_key');
            $this->assertEquals('test_value', $value, 'Cache connection successful');
        } catch (\Exception $e) {
            $this->fail('Cache connection failed: ' . $e->getMessage());
        }
    }

    public function test_api_health()
    {
        $response = $this->get('/health');
        $response->assertStatus(200);
        $response->assertJson([
            'status' => 'healthy',
            'services' => [
                'database' => true,
                'redis' => true,
                'cache' => true
            ]
        ]);
    }

    public function test_frontend_health()
    {
        $response = $this->get('/api/health');
        $response->assertStatus(200);
        $response->assertJsonStructure([
            'status',
            'version',
            'environment'
        ]);
    }
}
