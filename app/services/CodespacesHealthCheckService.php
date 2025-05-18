<?php

namespace App\Services;

use Illuminate\Support\Facades\Config;
use Illuminate\Support\Facades\File;
use Illuminate\Support\Facades\Log;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Redis;

class CodespacesHealthCheckService
{
    protected $logPath;
    protected $requiredServices = ['mysql', 'redis'];
    protected $healthStatus = [];

    public function __construct()
    {
        $this->logPath = Config::get('codespaces.paths.logs', '.codespaces/logs');
        $this->ensureLogDirectoryExists();
    }

    protected function ensureLogDirectoryExists(): void
    {
        if (!File::exists($this->logPath)) {
            File::makeDirectory($this->logPath, 0755, true);
        }
    }

    public function checkAllServices(): bool
    {
        $allHealthy = true;
        $this->healthStatus = [];

        foreach ($this->requiredServices as $service) {
            $isHealthy = $this->checkService($service);
            $this->healthStatus[$service] = $isHealthy;
            $allHealthy = $allHealthy && $isHealthy;
        }

        $this->logHealthCheckResults();
        return $allHealthy;
    }

    protected function checkService(string $service): bool
    {
        try {
            return match ($service) {
                'mysql' => $this->checkMySQL(),
                'redis' => $this->checkRedis(),
                default => false,
            };
        } catch (\Exception $e) {
            $this->logError($service, $e->getMessage());
            return false;
        }
    }

    protected function checkMySQL(): bool
    {
        try {
            DB::connection()->getPdo();
            return true;
        } catch (\Exception $e) {
            $this->logError('mysql', $e->getMessage());
            return false;
        }
    }

    protected function checkRedis(): bool
    {
        try {
            if (!extension_loaded('redis')) {
                $this->logError('redis', 'Redis extension not installed');
                return false;
            }
            Redis::ping();
            return true;
        } catch (\Exception $e) {
            $this->logError('redis', $e->getMessage());
            return false;
        }
    }

    protected function logHealthCheckResults(): void
    {
        $timestamp = now()->toIso8601String();
        $logFile = "{$this->logPath}/health_check.log";

        $results = array_map(
            fn($status) => $status ? 'healthy' : 'unhealthy',
            $this->healthStatus
        );

        $logMessage = "[{$timestamp}] Health Check Results:\n";
        foreach ($results as $service => $status) {
            $logMessage .= "{$service}: {$status}\n";
        }

        File::append($logFile, $logMessage);
    }

    protected function logError(string $service, string $error): void
    {
        $timestamp = now()->toIso8601String();
        $logFile = "{$this->logPath}/health_check_errors.log";
        $message = "[{$timestamp}] {$service} health check failed: {$error}\n";
        File::append($logFile, $message);
    }

    public function getHealthStatus(): array
    {
        return $this->healthStatus;
    }
}
