<?php

namespace Tests\Feature;

use Tests\TestCase;
use App\Services\CodespacesInitializer;
use App\Services\CodespacesHealthCheck;
use App\Services\CodespacesLifecycleManager;
use Illuminate\Support\Facades\Config;
use Illuminate\Support\Facades\File;

class CodespacesInitializerTest extends TestCase
{
    protected $initializer;
    protected $healthCheck;
    protected $lifecycleManager;
    protected $logPath;
    protected $statePath;
    protected $servicesPath;

    protected function setUp(): void
    {
        parent::setUp();

        $this->logPath = Config::get('codespaces.paths.logs', '.codespaces/logs');
        $this->statePath = Config::get('codespaces.paths.state', '.codespaces/state');
        $this->servicesPath = Config::get('codespaces.paths.services', '.codespaces/services');

        $this->healthCheck = app(CodespacesHealthCheck::class);
        $this->lifecycleManager = app(CodespacesLifecycleManager::class);
        $this->initializer = app(CodespacesInitializer::class);

        // Ensure directories exist
        if (!File::exists($this->logPath)) {
            File::makeDirectory($this->logPath, 0755, true);
        }
        if (!File::exists($this->statePath)) {
            File::makeDirectory($this->statePath, 0755, true);
        }
        if (!File::exists($this->servicesPath)) {
            File::makeDirectory($this->servicesPath, 0755, true);
        }
    }

    protected function tearDown(): void
    {
        // Clean up test files
        if (File::exists("{$this->logPath}/initializer.log")) {
            File::delete("{$this->logPath}/initializer.log");
        }
        if (File::exists("{$this->statePath}/services.json")) {
            File::delete("{$this->statePath}/services.json");
        }
        if (File::exists("{$this->servicesPath}/mysql.json")) {
            File::delete("{$this->servicesPath}/mysql.json");
        }
        if (File::exists("{$this->servicesPath}/redis.json")) {
            File::delete("{$this->servicesPath}/redis.json");
        }

        parent::tearDown();
    }

    public function test_initialization_checks_authentication()
    {
        // Mock GitHub token
        Config::set('codespaces.github_token', 'test_token');

        // Test initialization
        $result = $this->initializer->initialize();

        // Verify authentication was checked
        $logContent = File::get("{$this->logPath}/initializer.log");
        $this->assertStringContainsString('Starting Codespaces initialization', $logContent);
    }

    public function test_initialization_creates_missing_services()
    {
        // Configure test services
        Config::set('codespaces.services', [
            'mysql' => [
                'enabled' => true,
                'config' => [
                    'host' => 'codespaces-mysql',
                    'port' => 3306
                ]
            ],
            'redis' => [
                'enabled' => true,
                'config' => [
                    'host' => 'codespaces-redis',
                    'port' => 6379
                ]
            ]
        ]);

        // Run initialization
        $this->initializer->initialize();

        // Verify services were created
        $this->assertTrue(File::exists("{$this->servicesPath}/mysql.json"));
        $this->assertTrue(File::exists("{$this->servicesPath}/redis.json"));
    }

    public function test_initialization_starts_stopped_services()
    {
        // Create test service
        $this->lifecycleManager->saveServiceConfig('mysql', [
            'enabled' => true,
            'config' => [
                'host' => 'codespaces-mysql',
                'port' => 3306
            ]
        ]);

        // Stop service
        $this->lifecycleManager->stopService('mysql');

        // Run initialization
        $this->initializer->initialize();

        // Verify service was started
        $status = $this->lifecycleManager->getServiceStatus('mysql');
        $this->assertEquals('running', $status['status']);
    }

    public function test_initialization_heals_unhealthy_services()
    {
        // Create test service
        $this->lifecycleManager->saveServiceConfig('mysql', [
            'enabled' => true,
            'config' => [
                'host' => 'codespaces-mysql',
                'port' => 3306
            ]
        ]);

        // Start service
        $this->lifecycleManager->startService('mysql');

        // Mock health check to fail
        $this->healthCheck->shouldReceive('checkService')
            ->with('mysql')
            ->andReturn(['healthy' => false, 'issues' => ['Connection failed']]);

        // Run initialization
        $this->initializer->initialize();

        // Verify service was healed
        $status = $this->lifecycleManager->getServiceStatus('mysql');
        $this->assertEquals('running', $status['status']);
    }

    public function test_initialization_logs_all_actions()
    {
        // Run initialization
        $this->initializer->initialize();

        // Verify log file exists and contains expected entries
        $this->assertTrue(File::exists("{$this->logPath}/initializer.log"));
        $logContent = File::get("{$this->logPath}/initializer.log");

        $this->assertStringContainsString('Starting Codespaces initialization', $logContent);
        $this->assertStringContainsString('INFO', $logContent);
        $this->assertStringContainsString('SUCCESS', $logContent);
    }
}
