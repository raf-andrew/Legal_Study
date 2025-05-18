<?php

namespace Mcp\Discovery;

use Illuminate\Support\Collection;
use Illuminate\Support\Facades\Cache;
use Illuminate\Support\Facades\Log;

class ServiceHealthMonitor
{
    /**
     * @var Collection
     */
    protected $healthMetrics;

    /**
     * @var string
     */
    protected $cacheKey = 'mcp_service_health';

    /**
     * @var int
     */
    protected $cacheTtl = 300; // 5 minutes

    /**
     * @var array
     */
    protected $thresholds = [
        'response_time' => 1000, // milliseconds
        'error_rate' => 0.05, // 5%
        'memory_usage' => 128, // MB
    ];

    /**
     * ServiceHealthMonitor constructor.
     */
    public function __construct()
    {
        $this->healthMetrics = new Collection();
        $this->loadFromCache();
    }

    /**
     * Record a service call
     *
     * @param string $serviceClass
     * @param string $method
     * @param float $startTime
     * @param float $endTime
     * @param bool $success
     * @param int $memoryUsage
     */
    public function recordCall(
        string $serviceClass,
        string $method,
        float $startTime,
        float $endTime,
        bool $success,
        int $memoryUsage
    ): void {
        $responseTime = ($endTime - $startTime) * 1000; // Convert to milliseconds
        $key = $this->getMetricKey($serviceClass, $method);

        $metrics = $this->healthMetrics->get($key, [
            'calls' => 0,
            'successes' => 0,
            'errors' => 0,
            'total_response_time' => 0,
            'max_response_time' => 0,
            'total_memory_usage' => 0,
            'max_memory_usage' => 0,
            'last_updated' => time(),
        ]);

        $metrics['calls']++;
        $metrics['successes'] += $success ? 1 : 0;
        $metrics['errors'] += $success ? 0 : 1;
        $metrics['total_response_time'] += $responseTime;
        $metrics['max_response_time'] = max($metrics['max_response_time'], $responseTime);
        $metrics['total_memory_usage'] += $memoryUsage;
        $metrics['max_memory_usage'] = max($metrics['max_memory_usage'], $memoryUsage);
        $metrics['last_updated'] = time();

        $this->healthMetrics->put($key, $metrics);
        $this->saveToCache();

        $this->checkThresholds($serviceClass, $method, $metrics);
    }

    /**
     * Get service health metrics
     *
     * @param string $serviceClass
     * @param string|null $method
     * @return array|null
     */
    public function getHealthMetrics(string $serviceClass, ?string $method = null): ?array
    {
        $key = $this->getMetricKey($serviceClass, $method);
        return $this->healthMetrics->get($key);
    }

    /**
     * Get all health metrics
     *
     * @return Collection
     */
    public function getAllMetrics(): Collection
    {
        return $this->healthMetrics;
    }

    /**
     * Clear health metrics
     */
    public function clearMetrics(): void
    {
        $this->healthMetrics = new Collection();
        $this->saveToCache();
    }

    /**
     * Set threshold
     *
     * @param string $metric
     * @param float $value
     */
    public function setThreshold(string $metric, float $value): void
    {
        if (isset($this->thresholds[$metric])) {
            $this->thresholds[$metric] = $value;
        }
    }

    /**
     * Get threshold
     *
     * @param string $metric
     * @return float|null
     */
    public function getThreshold(string $metric): ?float
    {
        return $this->thresholds[$metric] ?? null;
    }

    /**
     * Get metric key
     *
     * @param string $serviceClass
     * @param string|null $method
     * @return string
     */
    protected function getMetricKey(string $serviceClass, ?string $method = null): string
    {
        return $method ? "{$serviceClass}::{$method}" : $serviceClass;
    }

    /**
     * Check thresholds and log warnings
     *
     * @param string $serviceClass
     * @param string $method
     * @param array $metrics
     */
    protected function checkThresholds(string $serviceClass, string $method, array $metrics): void
    {
        $errorRate = $metrics['errors'] / $metrics['calls'];
        $avgResponseTime = $metrics['total_response_time'] / $metrics['calls'];
        $avgMemoryUsage = $metrics['total_memory_usage'] / $metrics['calls'];

        if ($errorRate > $this->thresholds['error_rate']) {
            Log::warning("High error rate detected for {$serviceClass}::{$method}: {$errorRate}");
        }

        if ($avgResponseTime > $this->thresholds['response_time']) {
            Log::warning("High response time detected for {$serviceClass}::{$method}: {$avgResponseTime}ms");
        }

        if ($avgMemoryUsage > $this->thresholds['memory_usage']) {
            Log::warning("High memory usage detected for {$serviceClass}::{$method}: {$avgMemoryUsage}MB");
        }
    }

    /**
     * Load metrics from cache
     */
    protected function loadFromCache(): void
    {
        $cachedMetrics = Cache::get($this->cacheKey);

        if ($cachedMetrics) {
            $this->healthMetrics = new Collection($cachedMetrics);
        }
    }

    /**
     * Save metrics to cache
     */
    protected function saveToCache(): void
    {
        Cache::put($this->cacheKey, $this->healthMetrics->toArray(), $this->cacheTtl);
    }

    /**
     * Set cache TTL
     *
     * @param int $ttl
     */
    public function setCacheTtl(int $ttl): void
    {
        $this->cacheTtl = $ttl;
    }

    /**
     * Get cache TTL
     *
     * @return int
     */
    public function getCacheTtl(): int
    {
        return $this->cacheTtl;
    }
} 