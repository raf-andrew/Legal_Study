<?php

namespace Tests\Feature;

use Tests\TestCase;
use Illuminate\Support\Facades\Config;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Redis;
use Illuminate\Support\Facades\Cache;
use App\Services\CodespacesServiceManager;

class CodespacesHealthTest extends TestCase
{
    protected $serviceManager;

    protected function setUp(): void
    {
        parent::setUp();

        $this->serviceManager = app(CodespacesServiceManager::class);
        Config::set('codespaces.enabled', true);

        // Set up test service configurations
        $this->setUpTestServices();
    }

    protected function setUpTestServices(): void
    {
        // Set up MySQL service
        Config::set('database.connections.mysql', [
            'driver' => 'mysql',
            'host' => 'codespaces-mysql',
            'port' => 3306,
            'database' => 'legal_study',
            'username' => 'root',
            'password' => 'root',
            'charset' => 'utf8mb4',
            'collation' => 'utf8mb4_unicode_ci',
            'prefix' => '',
            'strict' => true,
            'engine' => null,
        ]);

        // Set up Redis service
        Config::set('database.redis.default', [
            'host' => 'codespaces-redis',
            'password' => null,
            'port' => 6379,
            'database' => 0,
        ]);

        // Set up cache and session
        Config::set('cache.default', 'redis');
        Config::set('session.driver', 'redis');
        Config::set('queue.default', 'redis');
    }

    public function test_codespaces_configuration()
    {
        $this->assertTrue(Config::get('codespaces.enabled'));
        $this->assertEquals('codespaces-mysql', Config::get('database.connections.mysql.host'));
        $this->assertEquals('codespaces-redis', Config::get('database.redis.default.host'));
    }

    public function test_database_connection()
    {
        try {
            DB::connection()->getPdo();
            $this->assertTrue(true);
        } catch (\Exception $e) {
            $this->fail('Database connection failed: ' . $e->getMessage());
        }
    }

    public function test_redis_connection()
    {
        try {
            Redis::ping();
            $this->assertTrue(true);
        } catch (\Exception $e) {
            $this->fail('Redis connection failed: ' . $e->getMessage());
        }
    }

    public function test_cache_connection()
    {
        try {
            $key = 'test_key_' . time();
            $value = 'test_value';

            Cache::put($key, $value, 60);
            $this->assertEquals($value, Cache::get($key));

            Cache::forget($key);
            $this->assertNull(Cache::get($key));
        } catch (\Exception $e) {
            $this->fail('Cache connection failed: ' . $e->getMessage());
        }
    }

    public function test_service_configuration()
    {
        $this->assertEquals('mysql', Config::get('database.default'));
        $this->assertEquals('redis', Config::get('cache.default'));
        $this->assertEquals('redis', Config::get('session.driver'));
        $this->assertEquals('redis', Config::get('queue.default'));
    }
}
