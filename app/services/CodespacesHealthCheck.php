<?php

namespace App\Services;

use Illuminate\Support\Facades\Config;
use Illuminate\Support\Facades\File;
use Illuminate\Support\Facades\Log;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Redis;

class CodespacesHealthCheck
{
    protected $logPath;
    protected $services;

    public function __construct()
    {
        $this->logPath = Config::get('codespaces.paths.logs');
        $this->services = Config::get('codespaces.services');
    }

    public function checkAll()
    {
        $results = [];

        foreach ($this->services as $service => $config) {
            if ($config['enabled']) {
                $results[$service] = $this->checkService($service);
            }
        }

        $this->logResults($results);
        return $results;
    }

    protected function checkService($service)
    {
        $method = 'check' . ucfirst($service);
        if (method_exists($this, $method)) {
            return $this->$method();
        }

        return [
            'status' => 'unknown',
            'message' => "Unknown service: {$service}"
        ];
    }

    protected function checkMysql()
    {
        try {
            DB::connection()->getPdo();
            return [
                'status' => 'healthy',
                'message' => 'MySQL connection successful'
            ];
        } catch (\Exception $e) {
            return [
                'status' => 'unhealthy',
                'message' => $e->getMessage()
            ];
        }
    }

    protected function checkRedis()
    {
        try {
            Redis::ping();
            return [
                'status' => 'healthy',
                'message' => 'Redis connection successful'
            ];
        } catch (\Exception $e) {
            return [
                'status' => 'unhealthy',
                'message' => $e->getMessage()
            ];
        }
    }

    protected function logResults($results)
    {
        $timestamp = now()->format('Y-m-d_H-i-s');
        $logFile = "{$this->logPath}/health_check_{$timestamp}.log";

        $logContent = json_encode([
            'timestamp' => now()->toIso8601String(),
            'results' => $results
        ], JSON_PRETTY_PRINT);

        file_put_contents($logFile, $logContent);

        // If all services are healthy, move log to complete folder
        $allHealthy = collect($results)->every(function ($result) {
            return $result['status'] === 'healthy';
        });

        if ($allHealthy) {
            $completePath = Config::get('codespaces.paths.complete');
            $completeFile = "{$completePath}/health_check_{$timestamp}.complete";
            rename($logFile, $completeFile);
        }
    }
}

