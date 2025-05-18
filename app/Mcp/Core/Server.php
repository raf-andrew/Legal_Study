<?php

namespace App\Mcp\Core;

use Illuminate\Support\Facades\Config;
use Illuminate\Support\Facades\Log;
use Illuminate\Support\Facades\Cache;

class Server
{
    protected bool $isEnabled = false;
    protected bool $isProduction = false;
    protected array $services = [];
    protected array $config = [];
    protected array $healthMetrics = [];

    public function __construct()
    {
        $this->initialize();
    }

    protected function initialize(): void
    {
        $this->isProduction = app()->environment('production');
        $this->isEnabled = !$this->isProduction || Config::get('mcp.enabled', false);
        
        if ($this->isEnabled) {
            $this->loadConfiguration();
            $this->initializeServices();
            $this->startHealthMonitoring();
        }
    }

    protected function loadConfiguration(): void
    {
        $this->config = Config::get('mcp', []);
        
        if (empty($this->config)) {
            Log::warning('MCP configuration not found. Using default settings.');
            $this->config = $this->getDefaultConfig();
        }
    }

    protected function getDefaultConfig(): array
    {
        return [
            'enabled' => !$this->isProduction,
            'debug' => !$this->isProduction,
            'services' => [],
            'security' => [
                'enabled' => true,
                'allowed_ips' => [],
                'api_key' => null,
            ],
            'monitoring' => [
                'interval' => 60,
                'metrics' => ['cpu', 'memory', 'disk'],
            ],
        ];
    }

    protected function initializeServices(): void
    {
        foreach ($this->config['services'] ?? [] as $service => $config) {
            $this->registerService($service, $config);
        }
    }

    public function registerService(string $name, array $config): bool
    {
        if (isset($this->services[$name])) {
            Log::warning("Service {$name} is already registered.");
            return false;
        }

        $this->services[$name] = [
            'config' => $config,
            'status' => 'initializing',
            'last_check' => now(),
            'metrics' => [],
        ];

        Log::info("Service {$name} registered successfully.");
        return true;
    }

    protected function startHealthMonitoring(): void
    {
        $this->updateHealthMetrics();
        
        // Schedule periodic health checks
        Cache::remember('mcp_health_check', $this->config['monitoring']['interval'] ?? 60, function () {
            $this->updateHealthMetrics();
            return true;
        });
    }

    protected function updateHealthMetrics(): void
    {
        $this->healthMetrics = [
            'timestamp' => now(),
            'cpu_usage' => $this->getCpuUsage(),
            'memory_usage' => $this->getMemoryUsage(),
            'disk_usage' => $this->getDiskUsage(),
            'services' => $this->getServiceStatuses(),
        ];
    }

    protected function getCpuUsage(): float
    {
        if (function_exists('sys_getloadavg')) {
            $load = sys_getloadavg();
            return $load[0] ?? 0.0;
        }
        return 0.0;
    }

    protected function getMemoryUsage(): array
    {
        return [
            'total' => memory_get_usage(true),
            'peak' => memory_get_peak_usage(true),
        ];
    }

    protected function getDiskUsage(): array
    {
        $total = disk_total_space('/');
        $free = disk_free_space('/');
        
        return [
            'total' => $total,
            'free' => $free,
            'used' => $total - $free,
            'percentage' => $total > 0 ? (($total - $free) / $total) * 100 : 0,
        ];
    }

    protected function getServiceStatuses(): array
    {
        $statuses = [];
        foreach ($this->services as $name => $service) {
            $statuses[$name] = [
                'status' => $service['status'],
                'last_check' => $service['last_check'],
                'metrics' => $service['metrics'],
            ];
        }
        return $statuses;
    }

    public function isEnabled(): bool
    {
        return $this->isEnabled;
    }

    public function isProduction(): bool
    {
        return $this->isProduction;
    }

    public function getConfig(): array
    {
        return $this->config;
    }

    public function getHealthMetrics(): array
    {
        return $this->healthMetrics;
    }

    public function getServices(): array
    {
        return $this->services;
    }
} 