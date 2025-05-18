<?php

namespace Tests\Feature;

use Tests\TestCase;
use App\Services\CodespacesHealthCheck;
use Illuminate\Support\Facades\Config;
use Illuminate\Support\Facades\File;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Redis;
use Illuminate\Support\Facades\Http;

class CodespacesHealthCheckTest extends TestCase
{
    protected $healthCheck;
    protected $logPath;

    protected function setUp(): void
    {
        parent::setUp();

        $this->healthCheck = new CodespacesHealthCheck();
        $this->logPath = Config::get('codespaces.paths.logs');

        // Ensure log directory exists
        if (!File::exists($this->logPath)) {
            File::makeDirectory($this->logPath, 0755, true);
        }
    }

    protected function tearDown(): void
    {
        // Clean up test files
        $files = File::glob("{$this->logPath}/*");
        foreach ($files as $file) {
            File::delete($file);
        }

        parent::tearDown();
    }

    public function test_health_check_logs_actions()
    {
        $results = $this->healthCheck->checkAll();

        $this->assertIsArray($results);
        $this->assertNotEmpty($results);

        // Verify log file was created
        $files = File::glob("{$this->logPath}/health_check_*.log");
        $this->assertCount(1, $files);

        $logContent = json_decode(File::get($files[0]), true);
        $this->assertIsArray($logContent);
        $this->assertArrayHasKey('timestamp', $logContent);
        $this->assertArrayHasKey('results', $logContent);
    }

    public function test_mysql_health_check()
    {
        // Mock DB connection
        DB::shouldReceive('connection->getPdo')
            ->once()
            ->andReturn(new \PDO('sqlite::memory:'));

        $result = $this->healthCheck->checkAll();

        $this->assertArrayHasKey('mysql', $result);
        $this->assertEquals('healthy', $result['mysql']['status']);
    }

    public function test_redis_health_check()
    {
        // Mock Redis connection
        Redis::shouldReceive('ping')
            ->once()
            ->andReturn('PONG');

        $result = $this->healthCheck->checkAll();

        $this->assertArrayHasKey('redis', $result);
        $this->assertEquals('healthy', $result['redis']['status']);
    }

    public function test_unknown_service_health_check()
    {
        Config::set('codespaces.services.unknown', [
            'enabled' => true
        ]);

        $result = $this->healthCheck->checkAll();

        $this->assertArrayHasKey('unknown', $result);
        $this->assertEquals('unknown', $result['unknown']['status']);
    }

    public function test_mysql_health_check_failure()
    {
        // Mock DB connection failure
        DB::shouldReceive('connection->getPdo')
            ->once()
            ->andThrow(new \Exception('Connection failed'));

        $result = $this->healthCheck->checkAll();

        $this->assertArrayHasKey('mysql', $result);
        $this->assertEquals('unhealthy', $result['mysql']['status']);
        $this->assertStringContainsString('Connection failed', $result['mysql']['message']);
    }

    public function test_redis_health_check_failure()
    {
        // Mock Redis connection failure
        Redis::shouldReceive('ping')
            ->once()
            ->andThrow(new \Exception('Connection failed'));

        $result = $this->healthCheck->checkAll();

        $this->assertArrayHasKey('redis', $result);
        $this->assertEquals('unhealthy', $result['redis']['status']);
        $this->assertStringContainsString('Connection failed', $result['redis']['message']);
    }
}

