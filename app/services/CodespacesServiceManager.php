<?php

namespace App\Services;

use Illuminate\Support\Facades\Config;
use Illuminate\Support\Facades\File;
use Illuminate\Support\Facades\Log;

class CodespacesServiceManager
{
    protected $servicesPath;
    protected $statePath;
    protected $logPath;

    public function __construct()
    {
        $this->servicesPath = Config::get('codespaces.paths.services', '.codespaces/services');
        $this->statePath = Config::get('codespaces.paths.state', '.codespaces/state');
        $this->logPath = Config::get('codespaces.paths.logs', '.codespaces/logs');

        $this->ensureDirectoriesExist();
    }

    protected function ensureDirectoriesExist(): void
    {
        $directories = [
            $this->servicesPath,
            $this->statePath,
            $this->logPath,
            '.codespaces/complete',
            '.codespaces/verification'
        ];

        foreach ($directories as $directory) {
            if (!File::exists($directory)) {
                File::makeDirectory($directory, 0755, true);
            }
        }
    }

    public function enableService(string $service): bool
    {
        try {
            $config = $this->loadServiceConfig($service);
            if (!$config) {
                return false;
            }

            $config['enabled'] = true;
            $this->saveServiceConfig($service, $config);
            $this->logServiceAction($service, 'enabled');
            return true;
        } catch (\Exception $e) {
            $this->logError($service, 'enable', $e->getMessage());
            return false;
        }
    }

    public function disableService(string $service): bool
    {
        try {
            $config = $this->loadServiceConfig($service);
            if (!$config) {
                return false;
            }

            $config['enabled'] = false;
            $this->saveServiceConfig($service, $config);
            $this->logServiceAction($service, 'disabled');
            return true;
        } catch (\Exception $e) {
            $this->logError($service, 'disable', $e->getMessage());
            return false;
        }
    }

    public function isServiceEnabled(string $service): bool
    {
        $config = $this->loadServiceConfig($service);
        return $config && ($config['enabled'] ?? false);
    }

    public function loadServiceConfig(string $service): ?array
    {
        $configFile = "{$this->servicesPath}/{$service}.json";
        if (!File::exists($configFile)) {
            return null;
        }

        return json_decode(File::get($configFile), true);
    }

    protected function saveServiceConfig(string $service, array $config): void
    {
        $configFile = "{$this->servicesPath}/{$service}.json";
        File::put($configFile, json_encode($config, JSON_PRETTY_PRINT));
    }

    public function overrideConfig(): void
    {
        if (!Config::get('codespaces.enabled', false)) {
            return;
        }

        // Load all service configs from .codespaces/services/
        $serviceFiles = File::glob($this->servicesPath . '/*.json');
        foreach ($serviceFiles as $file) {
            $config = json_decode(File::get($file), true);
            if ($config && ($config['enabled'] ?? false)) {
                $this->applyServiceConfig($config['service'], $config);
            }
        }
    }

    protected function applyServiceConfig(string $service, array $config): void
    {
        switch ($service) {
            case 'mysql':
                Config::set('database.connections.mysql', array_merge(
                    Config::get('database.connections.mysql', []),
                    $config['config'] ?? []
                ));
                break;
            case 'redis':
                Config::set('database.redis.default', array_merge(
                    Config::get('database.redis.default', []),
                    $config['config'] ?? []
                ));
                Config::set('cache.default', 'redis');
                Config::set('session.driver', 'redis');
                Config::set('queue.default', 'redis');
                break;
        }
    }

    protected function logServiceAction(string $service, string $action): void
    {
        $logFile = "{$this->logPath}/service_{$service}.log";
        $timestamp = now()->toIso8601String();
        $message = "[{$timestamp}] Service {$service} {$action}\n";
        File::append($logFile, $message);
    }

    protected function logError(string $service, string $action, string $error): void
    {
        $logFile = "{$this->logPath}/errors.log";
        $timestamp = now()->toIso8601String();
        $message = "[{$timestamp}] Error {$action} service {$service}: {$error}\n";
        File::append($logFile, $message);
    }
}
