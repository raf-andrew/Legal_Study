<?php

namespace Tests\Feature;

use Tests\TestCase;
use App\Services\CodespacesServiceManager;
use App\Services\CodespacesHealthCheck;
use App\Services\CodespacesLifecycleManager;
use Illuminate\Support\Facades\File;
use Illuminate\Support\Facades\Config;
use Illuminate\Support\Facades\Http;

class CodespacesLifecycleTest extends TestCase
{
    protected $serviceManager;
    protected $healthCheck;
    protected $lifecycleManager;
    protected $servicesPath;
    protected $statePath;
    protected $logPath;

    protected function setUp(): void
    {
        parent::setUp();

        $this->servicesPath = '.codespaces/services';
        $this->statePath = '.codespaces/state';
        $this->logPath = Config::get('codespaces.paths.logs', '.codespaces/logs');

        $this->serviceManager = app(CodespacesServiceManager::class);
        $this->healthCheck = app(CodespacesHealthCheck::class);
        $this->lifecycleManager = app(CodespacesLifecycleManager::class);

        // Ensure directories exist
        if (!File::exists($this->servicesPath)) {
            File::makeDirectory($this->servicesPath, 0755, true);
        }
        if (!File::exists($this->statePath)) {
            File::makeDirectory($this->statePath, 0755, true);
        }
    }

    protected function tearDown(): void
    {
        // Clean up directories
        if (File::exists($this->servicesPath)) {
            File::deleteDirectory($this->servicesPath);
        }
        if (File::exists($this->statePath)) {
            File::deleteDirectory($this->statePath);
        }
        if (File::exists("{$this->logPath}/lifecycle_mysql.log")) {
            File::delete("{$this->logPath}/lifecycle_mysql.log");
        }
        if (File::exists("{$this->logPath}/lifecycle_redis.log")) {
            File::delete("{$this->logPath}/lifecycle_redis.log");
        }

        parent::tearDown();
    }

    public function test_service_state_is_persisted()
    {
        // Create test service file
        $serviceConfig = [
            'service' => 'mysql',
            'enabled' => true,
            'config' => [
                'host' => 'codespaces-mysql',
                'port' => 3306,
                'database' => 'legal_study',
                'username' => 'root',
                'password' => 'root'
            ]
        ];

        File::put(
            "{$this->servicesPath}/mysql.json",
            json_encode($serviceConfig, JSON_PRETTY_PRINT)
        );

        // Save service state
        $this->lifecycleManager->saveServiceState('mysql', [
            'status' => 'running',
            'created_at' => now()->toIso8601String()
        ]);

        // Verify state was saved
        $state = $this->lifecycleManager->getServiceState('mysql');
        $this->assertNotNull($state);
        $this->assertEquals('running', $state['status']);
    }

    public function test_service_state_is_merged()
    {
        // Create initial state
        $this->lifecycleManager->saveServiceState('mysql', [
            'status' => 'running',
            'created_at' => now()->toIso8601String()
        ]);

        // Update state
        $this->lifecycleManager->saveServiceState('mysql', [
            'status' => 'stopped',
            'stopped_at' => now()->toIso8601String()
        ]);

        // Verify state was merged
        $state = $this->lifecycleManager->getServiceState('mysql');
        $this->assertEquals('stopped', $state['status']);
        $this->assertNotNull($state['created_at']);
        $this->assertNotNull($state['stopped_at']);
    }

    public function test_service_config_is_loaded()
    {
        // Create test service file
        $serviceConfig = [
            'service' => 'mysql',
            'enabled' => true,
            'config' => [
                'host' => 'test-host',
                'port' => 3306,
                'database' => 'test-db',
                'username' => 'test-user',
                'password' => 'test-pass'
            ]
        ];

        File::put(
            "{$this->servicesPath}/mysql.json",
            json_encode($serviceConfig, JSON_PRETTY_PRINT)
        );

        // Load config
        $config = $this->lifecycleManager->loadServiceConfig('mysql');
        $this->assertNotNull($config);
        $this->assertEquals('test-host', $config['config']['host']);
        $this->assertEquals(3306, $config['config']['port']);
    }

    public function test_service_creation_updates_state()
    {
        // Create test service file
        $serviceConfig = [
            'service' => 'mysql',
            'enabled' => true,
            'config' => [
                'host' => 'codespaces-mysql',
                'port' => 3306,
                'database' => 'legal_study',
                'username' => 'root',
                'password' => 'root'
            ]
        ];

        File::put(
            "{$this->servicesPath}/mysql.json",
            json_encode($serviceConfig, JSON_PRETTY_PRINT)
        );

        // Create service
        $this->lifecycleManager->createService('mysql');

        // Verify state was updated
        $state = $this->lifecycleManager->getServiceState('mysql');
        $this->assertNotNull($state);
        $this->assertEquals('running', $state['status']);
        $this->assertNotNull($state['created_at']);
        $this->assertEquals('healthy', $state['health_status']);
    }

    public function test_service_teardown_updates_state()
    {
        // Create test service file and initial state
        $serviceConfig = [
            'service' => 'mysql',
            'enabled' => true,
            'config' => [
                'host' => 'codespaces-mysql',
                'port' => 3306,
                'database' => 'legal_study',
                'username' => 'root',
                'password' => 'root'
            ]
        ];

        File::put(
            "{$this->servicesPath}/mysql.json",
            json_encode($serviceConfig, JSON_PRETTY_PRINT)
        );

        $this->lifecycleManager->saveServiceState('mysql', [
            'status' => 'running',
            'created_at' => now()->toIso8601String()
        ]);

        // Teardown service
        $this->lifecycleManager->teardownService('mysql');

        // Verify state was updated
        $state = $this->lifecycleManager->getServiceState('mysql');
        $this->assertNotNull($state);
        $this->assertEquals('stopped', $state['status']);
        $this->assertNotNull($state['stopped_at']);
    }

    public function test_service_lifecycle_management()
    {
        // Test MySQL service
        $this->assertTrue($this->lifecycleManager->startService('mysql'));
        $this->assertEquals('running', $this->lifecycleManager->getServiceStatus('mysql')['status']);

        $this->assertTrue($this->lifecycleManager->stopService('mysql'));
        $this->assertEquals('stopped', $this->lifecycleManager->getServiceStatus('mysql')['status']);

        $this->assertTrue($this->lifecycleManager->restartService('mysql'));
        $this->assertEquals('running', $this->lifecycleManager->getServiceStatus('mysql')['status']);

        // Test Redis service
        $this->assertTrue($this->lifecycleManager->startService('redis'));
        $this->assertEquals('running', $this->lifecycleManager->getServiceStatus('redis')['status']);

        $this->assertTrue($this->lifecycleManager->stopService('redis'));
        $this->assertEquals('stopped', $this->lifecycleManager->getServiceStatus('redis')['status']);

        $this->assertTrue($this->lifecycleManager->restartService('redis'));
        $this->assertEquals('running', $this->lifecycleManager->getServiceStatus('redis')['status']);
    }

    public function test_service_state_persistence()
    {
        // Start MySQL service
        $this->lifecycleManager->startService('mysql');

        // Verify state file exists
        $stateFile = "{$this->statePath}/services.json";
        $this->assertTrue(File::exists($stateFile));

        // Verify state content
        $state = json_decode(File::get($stateFile), true);
        $this->assertArrayHasKey('mysql', $state);
        $this->assertEquals('running', $state['mysql']['status']);
    }

    public function test_service_logging()
    {
        // Start MySQL service
        $this->lifecycleManager->startService('mysql');

        // Verify log file exists
        $logFile = "{$this->logPath}/lifecycle_mysql.log";
        $this->assertTrue(File::exists($logFile));

        // Verify log content
        $logContent = File::get($logFile);
        $this->assertStringContainsString('SUCCESS: Service started successfully', $logContent);
    }

    public function test_invalid_service_handling()
    {
        // Test non-existent service
        $this->assertFalse($this->lifecycleManager->startService('invalid_service'));
        $this->assertNull($this->lifecycleManager->getServiceStatus('invalid_service'));
    }

    public function test_service_creation()
    {
        // Mock GitHub token
        Config::set('codespaces.github.token', 'test_token');
        Config::set('codespaces.github.repository_id', '123456');

        // Mock GitHub API response
        Http::fake([
            'api.github.com/*' => Http::response([
                'name' => 'mysql',
                'state' => 'created'
            ], 201)
        ]);

        // Create service configuration
        $config = [
            'enabled' => true,
            'config' => [
                'host' => 'codespaces-mysql',
                'port' => 3306
            ]
        ];
        $this->lifecycleManager->saveServiceConfig('mysql', $config);

        // Create service
        $result = $this->lifecycleManager->createService('mysql');

        // Verify result
        $this->assertTrue($result);
        $this->assertTrue(File::exists("{$this->statePath}/mysql.json"));

        $state = json_decode(File::get("{$this->statePath}/mysql.json"), true);
        $this->assertEquals('created', $state['status']);
        $this->assertArrayHasKey('created_at', $state);
        $this->assertEquals($config, $state['config']);
    }

    public function test_service_start()
    {
        // Mock GitHub token
        Config::set('codespaces.github.token', 'test_token');

        // Create service state
        $state = [
            'status' => 'stopped',
            'created_at' => now()->toIso8601String(),
            'config' => [
                'enabled' => true,
                'config' => [
                    'host' => 'codespaces-mysql',
                    'port' => 3306
                ]
            ]
        ];
        File::put("{$this->statePath}/mysql.json", json_encode($state));

        // Mock GitHub API response
        Http::fake([
            'api.github.com/*' => Http::response([
                'name' => 'mysql',
                'state' => 'running'
            ], 200)
        ]);

        // Start service
        $result = $this->lifecycleManager->startService('mysql');

        // Verify result
        $this->assertTrue($result);

        $state = json_decode(File::get("{$this->statePath}/mysql.json"), true);
        $this->assertEquals('running', $state['status']);
        $this->assertArrayHasKey('started_at', $state);
    }

    public function test_service_stop()
    {
        // Mock GitHub token
        Config::set('codespaces.github.token', 'test_token');

        // Create service state
        $state = [
            'status' => 'running',
            'created_at' => now()->toIso8601String(),
            'started_at' => now()->toIso8601String(),
            'config' => [
                'enabled' => true,
                'config' => [
                    'host' => 'codespaces-mysql',
                    'port' => 3306
                ]
            ]
        ];
        File::put("{$this->statePath}/mysql.json", json_encode($state));

        // Mock GitHub API response
        Http::fake([
            'api.github.com/*' => Http::response([
                'name' => 'mysql',
                'state' => 'stopped'
            ], 200)
        ]);

        // Stop service
        $result = $this->lifecycleManager->stopService('mysql');

        // Verify result
        $this->assertTrue($result);

        $state = json_decode(File::get("{$this->statePath}/mysql.json"), true);
        $this->assertEquals('stopped', $state['status']);
        $this->assertArrayHasKey('stopped_at', $state);
    }

    public function test_service_status()
    {
        // Mock GitHub token
        Config::set('codespaces.github.token', 'test_token');

        // Create service state
        $state = [
            'status' => 'running',
            'created_at' => now()->toIso8601String(),
            'started_at' => now()->toIso8601String(),
            'config' => [
                'enabled' => true,
                'config' => [
                    'host' => 'codespaces-mysql',
                    'port' => 3306
                ]
            ]
        ];
        File::put("{$this->statePath}/mysql.json", json_encode($state));

        // Mock GitHub API response
        Http::fake([
            'api.github.com/*' => Http::response([
                'name' => 'mysql',
                'state' => 'running'
            ], 200)
        ]);

        // Get service status
        $status = $this->lifecycleManager->getServiceStatus('mysql');

        // Verify result
        $this->assertNotNull($status);
        $this->assertEquals('mysql', $status['name']);
        $this->assertEquals('running', $status['status']);
        $this->assertArrayHasKey('created_at', $status);
        $this->assertArrayHasKey('started_at', $status);
        $this->assertArrayHasKey('config', $status);
    }

    public function test_service_config_management()
    {
        // Create service configuration
        $config = [
            'enabled' => true,
            'config' => [
                'host' => 'codespaces-mysql',
                'port' => 3306
            ]
        ];

        // Save configuration
        $this->lifecycleManager->saveServiceConfig('mysql', $config);

        // Verify configuration was saved
        $this->assertTrue(File::exists("{$this->servicesPath}/mysql.json"));

        $savedConfig = json_decode(File::get("{$this->servicesPath}/mysql.json"), true);
        $this->assertEquals($config, $savedConfig);

        // Get configuration
        $retrievedConfig = $this->lifecycleManager->getServiceConfig('mysql');
        $this->assertEquals($config, $retrievedConfig);
    }

    public function test_service_creation_failure()
    {
        // Mock GitHub token
        Config::set('codespaces.github.token', 'test_token');

        // Mock GitHub API failure
        Http::fake([
            'api.github.com/*' => Http::response([
                'message' => 'Invalid request'
            ], 400)
        ]);

        // Create service configuration
        $config = [
            'enabled' => true,
            'config' => [
                'host' => 'codespaces-mysql',
                'port' => 3306
            ]
        ];
        $this->lifecycleManager->saveServiceConfig('mysql', $config);

        // Attempt to create service
        $result = $this->lifecycleManager->createService('mysql');

        // Verify result
        $this->assertFalse($result);
        $this->assertFalse(File::exists("{$this->statePath}/mysql.json"));
    }

    public function test_service_start_failure()
    {
        // Mock GitHub token
        Config::set('codespaces.github.token', 'test_token');

        // Create service state
        $state = [
            'status' => 'stopped',
            'created_at' => now()->toIso8601String(),
            'config' => [
                'enabled' => true,
                'config' => [
                    'host' => 'codespaces-mysql',
                    'port' => 3306
                ]
            ]
        ];
        File::put("{$this->statePath}/mysql.json", json_encode($state));

        // Mock GitHub API failure
        Http::fake([
            'api.github.com/*' => Http::response([
                'message' => 'Service not found'
            ], 404)
        ]);

        // Attempt to start service
        $result = $this->lifecycleManager->startService('mysql');

        // Verify result
        $this->assertFalse($result);

        $state = json_decode(File::get("{$this->statePath}/mysql.json"), true);
        $this->assertEquals('stopped', $state['status']);
        $this->assertArrayNotHasKey('started_at', $state);
    }
}
