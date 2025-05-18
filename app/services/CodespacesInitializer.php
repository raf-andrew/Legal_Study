<?php

namespace App\Services;

use Illuminate\Support\Facades\Config;
use Illuminate\Support\Facades\File;
use Illuminate\Support\Facades\Log;
use Illuminate\Support\Facades\Http;

class CodespacesInitializer
{
    protected $healthCheck;
    protected $lifecycleManager;
    protected $logPath;
    protected $statePath;
    protected $servicesPath;

    public function __construct(
        CodespacesHealthCheck $healthCheck,
        CodespacesLifecycleManager $lifecycleManager
    ) {
        $this->healthCheck = $healthCheck;
        $this->lifecycleManager = $lifecycleManager;
        $this->logPath = Config::get('codespaces.paths.logs', '.codespaces/logs');
        $this->statePath = Config::get('codespaces.paths.state', '.codespaces/state');
        $this->servicesPath = Config::get('codespaces.paths.services', '.codespaces/services');
    }

    public function initialize(): bool
    {
        try {
            $this->logInfo('Starting Codespaces initialization');

            // Check authentication
            if (!$this->checkAuthentication()) {
                $this->logError('Authentication failed');
                return false;
            }

            // Initialize required services
            $services = Config::get('codespaces.services', []);
            foreach ($services as $name => $config) {
                if ($config['enabled'] ?? false) {
                    $this->initializeService($name, $config);
                }
            }

            // Run health checks
            $healthStatus = $this->healthCheck->checkAll();
            if (!$healthStatus['healthy']) {
                $this->logError('Health check failed: ' . json_encode($healthStatus['issues']));
                return false;
            }

            $this->logSuccess('Codespaces initialization completed successfully');
            return true;
        } catch (\Exception $e) {
            $this->logError('Initialization failed: ' . $e->getMessage());
            return false;
        }
    }

    protected function checkAuthentication(): bool
    {
        try {
            $token = Config::get('codespaces.github_token');
            if (!$token) {
                $this->logError('GitHub token not configured');
                return false;
            }

            // Test GitHub API access
            $response = Http::withToken($token)
                ->get('https://api.github.com/user');

            return $response->successful();
        } catch (\Exception $e) {
            $this->logError('Authentication check failed: ' . $e->getMessage());
            return false;
        }
    }

    protected function initializeService(string $name, array $config): void
    {
        $this->logInfo("Initializing service: $name");

        // Check if service exists in Codespaces
        if (!$this->serviceExists($name)) {
            $this->logInfo("Service $name does not exist, creating...");
            $this->createService($name, $config);
        }

        // Start service if not running
        $status = $this->lifecycleManager->getServiceStatus($name);
        if (!$status || $status['status'] !== 'running') {
            $this->logInfo("Starting service: $name");
            $this->lifecycleManager->startService($name);
        }

        // Verify service health
        $health = $this->healthCheck->checkService($name);
        if (!$health['healthy']) {
            $this->logError("Service $name health check failed: " . json_encode($health['issues']));
            $this->healService($name);
        }
    }

    protected function serviceExists(string $name): bool
    {
        $state = $this->lifecycleManager->getServiceState($name);
        return $state !== null;
    }

    protected function createService(string $name, array $config): void
    {
        // Save service configuration
        $this->lifecycleManager->saveServiceConfig($name, $config);

        // Create service in Codespaces
        $this->lifecycleManager->createService($name);

        // Wait for service to be ready
        $maxAttempts = 30;
        $attempt = 0;
        while ($attempt < $maxAttempts) {
            $health = $this->healthCheck->checkService($name);
            if ($health['healthy']) {
                break;
            }
            sleep(2);
            $attempt++;
        }

        if ($attempt >= $maxAttempts) {
            throw new \Exception("Service $name failed to become healthy after creation");
        }
    }

    protected function healService(string $name): void
    {
        $this->logInfo("Attempting to heal service: $name");

        // Stop service
        $this->lifecycleManager->stopService($name);

        // Wait for service to stop
        sleep(5);

        // Start service
        $this->lifecycleManager->startService($name);

        // Verify health after healing
        $health = $this->healthCheck->checkService($name);
        if (!$health['healthy']) {
            throw new \Exception("Service $name failed to heal: " . json_encode($health['issues']));
        }
    }

    protected function logInfo(string $message): void
    {
        $this->log('INFO', $message);
    }

    protected function logError(string $message): void
    {
        $this->log('ERROR', $message);
    }

    protected function logSuccess(string $message): void
    {
        $this->log('SUCCESS', $message);
    }

    protected function log(string $level, string $message): void
    {
        $logFile = "{$this->logPath}/initializer.log";
        $timestamp = date('Y-m-d H:i:s');
        $logMessage = "[$timestamp] [$level] $message\n";

        File::ensureDirectoryExists(dirname($logFile));
        File::append($logFile, $logMessage);

        Log::channel('codespaces')->$level($message);
    }
}
