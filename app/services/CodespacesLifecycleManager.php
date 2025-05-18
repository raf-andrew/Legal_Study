<?php

namespace App\Services;

use Illuminate\Support\Facades\Config;
use Illuminate\Support\Facades\File;
use Illuminate\Support\Facades\Log;
use Illuminate\Support\Facades\Process;
use Illuminate\Support\Facades\Http;

class CodespacesLifecycleManager
{
    protected $services = [];
    protected $statePath;
    protected $logPath;
    protected $servicesPath;
    protected $githubToken;

    public function __construct()
    {
        $this->statePath = Config::get('codespaces.paths.state', '.codespaces/state');
        $this->logPath = Config::get('codespaces.paths.logs', '.codespaces/logs');
        $this->servicesPath = Config::get('codespaces.paths.services', '.codespaces/services');
        $this->githubToken = Config::get('codespaces.github.token');

        $this->ensureDirectoriesExist();
        $this->initializeServices();
    }

    protected function ensureDirectoriesExist(): void
    {
        $directories = [
            $this->logPath,
            $this->statePath,
            $this->servicesPath
        ];

        foreach ($directories as $directory) {
            if (!File::exists($directory)) {
                File::makeDirectory($directory, 0755, true);
            }
        }
    }

    protected function initializeServices()
    {
        $services = Config::get('codespaces.services', []);
        foreach ($services as $name => $config) {
            if ($config['enabled'] ?? false) {
                $this->services[$name] = [
                    'config' => $config,
                    'status' => 'unknown',
                    'last_check' => null,
                    'health_score' => 0
                ];
            }
        }
    }

    public function startService(string $serviceName): bool
    {
        if (!isset($this->services[$serviceName])) {
            $this->logError($serviceName, "Service not found");
            return false;
        }

        try {
            $this->logInfo("Starting service: {$serviceName}");

            // Get service state
            $state = $this->getServiceState($serviceName);
            if (!$state) {
                throw new \Exception("Service not found: {$serviceName}");
            }

            // Start service in Codespaces
            $response = Http::withToken($this->githubToken)
                ->post("https://api.github.com/user/codespaces/{$serviceName}/start");

            if (!$response->successful()) {
                throw new \Exception("Failed to start service: {$response->body()}");
            }

            // Update service state
            $state['status'] = 'running';
            $state['started_at'] = now()->toIso8601String();
            $this->saveServiceState($serviceName, $state);

            $this->logSuccess("Service started successfully: {$serviceName}");
            return true;
        } catch (\Exception $e) {
            $this->logError($serviceName, "Failed to start service: " . $e->getMessage());
            return false;
        }
    }

    public function stopService(string $serviceName): bool
    {
        if (!isset($this->services[$serviceName])) {
            $this->logError($serviceName, "Service not found");
            return false;
        }

        try {
            $this->logInfo("Stopping service: {$serviceName}");

            // Get service state
            $state = $this->getServiceState($serviceName);
            if (!$state) {
                throw new \Exception("Service not found: {$serviceName}");
            }

            // Stop service in Codespaces
            $response = Http::withToken($this->githubToken)
                ->post("https://api.github.com/user/codespaces/{$serviceName}/stop");

            if (!$response->successful()) {
                throw new \Exception("Failed to stop service: {$response->body()}");
            }

            // Update service state
            $state['status'] = 'stopped';
            $state['stopped_at'] = now()->toIso8601String();
            $this->saveServiceState($serviceName, $state);

            $this->logSuccess("Service stopped successfully: {$serviceName}");
            return true;
        } catch (\Exception $e) {
            $this->logError($serviceName, "Failed to stop service: " . $e->getMessage());
            return false;
        }
    }

    public function restartService(string $serviceName): bool
    {
        if ($this->stopService($serviceName)) {
            return $this->startService($serviceName);
        }
        return false;
    }

    public function getServiceStatus(string $serviceName): ?array
    {
        try {
            // Get service state
            $state = $this->getServiceState($serviceName);
            if (!$state) {
                return null;
            }

            // Get current status from Codespaces
            $response = Http::withToken($this->githubToken)
                ->get("https://api.github.com/user/codespaces/{$serviceName}");

            if (!$response->successful()) {
                throw new \Exception("Failed to get service status: {$response->body()}");
            }

            $status = $response->json();
            return [
                'name' => $serviceName,
                'status' => $status['state'] ?? 'unknown',
                'created_at' => $state['created_at'],
                'started_at' => $state['started_at'] ?? null,
                'stopped_at' => $state['stopped_at'] ?? null,
                'config' => $state['config']
            ];
        } catch (\Exception $e) {
            $this->logError($serviceName, "Failed to get service status: " . $e->getMessage());
            return null;
        }
    }

    public function getAllServices(): array
    {
        return $this->services;
    }

    public function saveServiceState(string $serviceName, array $state): void
    {
        $stateFile = "{$this->statePath}/{$serviceName}.json";
        File::put($stateFile, json_encode($state, JSON_PRETTY_PRINT));
    }

    public function loadServiceConfig(string $serviceName): ?array
    {
        $configFile = "{$this->servicesPath}/{$serviceName}.json";
        if (!File::exists($configFile)) {
            return null;
        }

        return json_decode(File::get($configFile), true);
    }

    public function saveServiceConfig(string $serviceName, array $config): void
    {
        $configFile = "{$this->servicesPath}/{$serviceName}.json";
        File::put($configFile, json_encode($config, JSON_PRETTY_PRINT));
    }

    public function createService(string $serviceName): bool
    {
        try {
            $this->logInfo("Creating service: {$serviceName}");

            // Get service configuration
            $config = $this->getServiceConfig($serviceName);
            if (!$config) {
                throw new \Exception("Service configuration not found: {$serviceName}");
            }

            // Create service in Codespaces
            $response = Http::withToken($this->githubToken)
                ->post("https://api.github.com/user/codespaces", [
                    'name' => $serviceName,
                    'repository_id' => Config::get('codespaces.github.repository_id'),
                    'machine' => Config::get('codespaces.machine', 'basicLinux32gb'),
                    'location' => Config::get('codespaces.region', 'us-east-1'),
                    'devcontainer_path' => ".codespaces/devcontainer/{$serviceName}.json"
                ]);

            if (!$response->successful()) {
                throw new \Exception("Failed to create service: {$response->body()}");
            }

            // Save service state
            $this->saveServiceState($serviceName, [
                'status' => 'created',
                'created_at' => now()->toIso8601String(),
                'config' => $config
            ]);

            $this->logSuccess("Service created successfully: {$serviceName}");
            return true;
        } catch (\Exception $e) {
            $this->logError("Failed to create service {$serviceName}: {$e->getMessage()}");
            return false;
        }
    }

    public function teardownService(string $serviceName): bool
    {
        try {
            $state = $this->getServiceStatus($serviceName);
            if (!$state) {
                $this->logError($serviceName, "Service state not found");
                return false;
            }

            $this->saveServiceState($serviceName, array_merge($state, [
                'status' => 'stopped',
                'stopped_at' => now()->toIso8601String()
            ]));

            $this->logSuccess($serviceName, "Service stopped successfully");
            return true;
        } catch (\Exception $e) {
            $this->logError($serviceName, "Failed to stop service: " . $e->getMessage());
            return false;
        }
    }

    protected function getServiceState(string $serviceName): ?array
    {
        $stateFile = "{$this->statePath}/{$serviceName}.json";
        if (!File::exists($stateFile)) {
            return null;
        }
        return json_decode(File::get($stateFile), true);
    }

    protected function getServiceConfig(string $serviceName): ?array
    {
        $configFile = "{$this->servicesPath}/{$serviceName}.json";
        if (!File::exists($configFile)) {
            return null;
        }
        return json_decode(File::get($configFile), true);
    }

    protected function logInfo(string $message): void
    {
        $this->log('INFO', $message);
    }

    protected function logError(string $service, string $message): void
    {
        $logFile = "{$this->logPath}/lifecycle_{$service}.log";
        Log::error("[$service] $message");
        File::append($logFile, date('Y-m-d H:i:s') . " ERROR: $message\n");
    }

    protected function logSuccess(string $service, string $message): void
    {
        $logFile = "{$this->logPath}/lifecycle_{$service}.log";
        Log::info("[$service] $message");
        File::append($logFile, date('Y-m-d H:i:s') . " SUCCESS: $message\n");
    }

    public function markServiceComplete(string $service, array $metadata = []): void
    {
        $timestamp = now()->toIso8601String();
        $root = realpath(base_path());
        $completePath = $root . DIRECTORY_SEPARATOR . '.codespaces' . DIRECTORY_SEPARATOR . 'complete';
        $completeFile = $completePath . DIRECTORY_SEPARATOR . "{$service}_{$timestamp}.complete";

        // Ensure .codespaces/complete exists with all parent directories
        if (!file_exists($completePath)) {
            mkdir($completePath, 0755, true);
        }

        $data = array_merge([
            'service' => $service,
            'status' => 'complete',
            'timestamp' => $timestamp,
            'state' => $this->getServiceState($service)
        ], $metadata);

        file_put_contents($completeFile, json_encode($data, JSON_PRETTY_PRINT));
    }

    protected function log(string $level, string $message): void
    {
        $logFile = "{$this->logPath}/lifecycle.log";
        $timestamp = date('Y-m-d H:i:s');
        $logMessage = "[$timestamp] [$level] $message\n";

        File::ensureDirectoryExists(dirname($logFile));
        File::append($logFile, $logMessage);

        Log::channel('codespaces')->$level($message);
    }
}
