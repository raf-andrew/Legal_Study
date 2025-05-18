<?php

namespace Tests\Feature;

use Tests\TestCase;
use App\Services\CodespacesServiceManager;
use App\Services\CodespacesHealthCheck;
use App\Services\CodespacesLifecycleManager;
use Illuminate\Support\Facades\Config;
use Illuminate\Support\Facades\File;

class CodespacesServiceTest extends TestCase
{
    protected $serviceManager;
    protected $healthCheck;
    protected $lifecycleManager;
    protected $servicesPath;

    protected function setUp(): void
    {
        parent::setUp();

        $this->servicesPath = '.codespaces/services';
        $this->serviceManager = app(CodespacesServiceManager::class);
        $this->healthCheck = app(CodespacesHealthCheck::class);
        $this->lifecycleManager = app(CodespacesLifecycleManager::class);

        // Ensure services directory exists
        if (!File::exists($this->servicesPath)) {
            File::makeDirectory($this->servicesPath, 0755, true);
        }

        Config::set('codespaces.enabled', true);
    }

    protected function tearDown(): void
    {
        // Clean up service files
        if (File::exists($this->servicesPath)) {
            File::deleteDirectory($this->servicesPath);
        }
        // Do NOT delete .codespaces/complete so completion files persist
        parent::tearDown();
    }

    public function test_service_manager_can_enable_and_disable_services()
    {
        // Create test service file
        $serviceConfig = [
            'service' => 'mysql',
            'enabled' => false,
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

        // Test enabling service
        $this->assertTrue($this->serviceManager->enableService('mysql'));
        $this->assertTrue($this->serviceManager->isServiceEnabled('mysql'));

        // Test disabling service
        $this->assertTrue($this->serviceManager->disableService('mysql'));
        $this->assertFalse($this->serviceManager->isServiceEnabled('mysql'));
    }

    public function test_service_manager_overrides_config_when_enabled()
    {
        Config::set('codespaces.enabled', true);

        // Create and enable test service
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

        // Test config override
        $this->serviceManager->overrideConfig();

        $this->assertEquals('test-host', Config::get('database.connections.mysql.host'));
        $this->assertEquals(3306, Config::get('database.connections.mysql.port'));
        $this->assertEquals('test-db', Config::get('database.connections.mysql.database'));
        $this->assertEquals('test-user', Config::get('database.connections.mysql.username'));
        $this->assertEquals('test-pass', Config::get('database.connections.mysql.password'));
    }

    public function test_health_check_can_detect_service_status()
    {
        // Create and enable test service
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

        // Test health check
        $this->assertIsBool($this->healthCheck->checkServiceHealth('mysql'));
    }

    public function test_health_check_logs_service_status()
    {
        // Create and enable test service
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

        // Run health check
        $this->healthCheck->checkServiceHealth('mysql');

        // Verify log file exists
        $logFile = '.codespaces/logs/health_mysql.log';
        $this->assertTrue(File::exists($logFile));

        // Verify log content
        $logContent = File::get($logFile);
        $this->assertStringContainsString('Health check', $logContent);
    }

    public function test_service_configuration_is_loaded()
    {
        // Create test service configuration
        $config = [
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

        $this->lifecycleManager->saveServiceConfig('mysql', $config);

        // Verify configuration is loaded
        $loadedConfig = $this->serviceManager->loadServiceConfig('mysql');
        $this->assertNotNull($loadedConfig);
        $this->assertEquals('codespaces-mysql', $loadedConfig['config']['host']);
        $this->assertEquals(3306, $loadedConfig['config']['port']);
    }

    public function test_service_state_is_persisted()
    {
        // Create test service state
        $state = [
            'status' => 'running',
            'created_at' => now()->toIso8601String(),
            'health_status' => 'healthy'
        ];

        $this->lifecycleManager->saveServiceState('mysql', $state);

        // Verify state is persisted
        $loadedState = $this->lifecycleManager->getServiceState('mysql');
        $this->assertNotNull($loadedState);
        $this->assertEquals('running', $loadedState['status']);
        $this->assertEquals('healthy', $loadedState['health_status']);
    }

    public function test_service_health_check()
    {
        // Create test service configuration
        $config = [
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

        $this->lifecycleManager->saveServiceConfig('mysql', $config);

        // Perform health check
        $result = $this->healthCheck->checkServiceHealth('mysql');
        $this->assertIsBool($result);

        // Verify health check status
        $status = $this->healthCheck->getServiceStatus('mysql');
        $this->assertNotNull($status);
        $this->assertArrayHasKey('health', $status);
        $this->assertArrayHasKey('last_check', $status);
    }

    public function test_service_lifecycle()
    {
        // Create test service configuration
        $config = [
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

        $this->lifecycleManager->saveServiceConfig('mysql', $config);

        // Create service
        $this->assertTrue($this->lifecycleManager->createService('mysql'));

        // Verify service state
        $state = $this->lifecycleManager->getServiceState('mysql');
        $this->assertNotNull($state);
        $this->assertEquals('running', $state['status']);

        // Teardown service
        $this->assertTrue($this->lifecycleManager->teardownService('mysql'));

        // Verify service state
        $state = $this->lifecycleManager->getServiceState('mysql');
        $this->assertNotNull($state);
        $this->assertEquals('stopped', $state['status']);
    }

    public function test_service_completion()
    {
        // Ensure .codespaces/complete exists
        if (!File::exists('.codespaces/complete')) {
            File::makeDirectory('.codespaces/complete', 0755, true);
        }
        // Debug log
        file_put_contents('storage/logs/service_test_debug.log', "Before markServiceComplete: exists=" . (File::exists('.codespaces/complete') ? 'yes' : 'no') . ", writable=" . (is_writable('.codespaces/complete') ? 'yes' : 'no') . "\n", FILE_APPEND);
        // Create test service configuration
        $config = [
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

        $this->lifecycleManager->saveServiceConfig('mysql', $config);

        // Create service
        $this->assertTrue($this->lifecycleManager->createService('mysql'));

        // Mark service as complete
        $this->lifecycleManager->markServiceComplete('mysql', [
            'test_result' => 'passed',
            'test_name' => 'CodespacesServiceTest::test_service_completion'
        ]);
        // Debug log after
        file_put_contents('storage/logs/service_test_debug.log', "After markServiceComplete\n", FILE_APPEND);

        // Verify completion file exists
        $completeFiles = File::glob('.codespaces/complete/mysql_*.complete');
        $this->assertNotEmpty($completeFiles);

        // Verify completion data
        $completeData = json_decode(File::get($completeFiles[0]), true);
        $this->assertNotNull($completeData);
        $this->assertEquals('complete', $completeData['status']);
        $this->assertEquals('passed', $completeData['test_result']);
    }
}
