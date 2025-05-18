<?php

namespace Mcp\Discovery;

use Illuminate\Support\Collection;
use Illuminate\Support\Facades\Cache;

class ServiceRegistry
{
    /**
     * @var Collection
     */
    protected $services;

    /**
     * @var string
     */
    protected $cacheKey = 'mcp_service_registry';

    /**
     * @var int
     */
    protected $cacheTtl = 3600; // 1 hour

    /**
     * ServiceRegistry constructor.
     */
    public function __construct()
    {
        $this->services = new Collection();
        $this->loadFromCache();
    }

    /**
     * Register a service
     *
     * @param array $service
     * @return bool
     */
    public function register(array $service): bool
    {
        if (!$this->validateService($service)) {
            return false;
        }

        $this->services->push($service);
        $this->saveToCache();

        return true;
    }

    /**
     * Register multiple services
     *
     * @param array $services
     * @return int
     */
    public function registerMany(array $services): int
    {
        $count = 0;

        foreach ($services as $service) {
            if ($this->register($service)) {
                $count++;
            }
        }

        return $count;
    }

    /**
     * Unregister a service
     *
     * @param string $className
     * @return bool
     */
    public function unregister(string $className): bool
    {
        $count = $this->services->count();
        $this->services = $this->services->reject(function ($service) use ($className) {
            return $service['class'] === $className;
        });

        if ($this->services->count() !== $count) {
            $this->saveToCache();
            return true;
        }

        return false;
    }

    /**
     * Find a service by class name
     *
     * @param string $className
     * @return array|null
     */
    public function find(string $className): ?array
    {
        return $this->services->first(function ($service) use ($className) {
            return $service['class'] === $className;
        });
    }

    /**
     * Find services by type
     *
     * @param string $type
     * @return Collection
     */
    public function findByType(string $type): Collection
    {
        return $this->services->filter(function ($service) use ($type) {
            return isset($service['metadata']['interfaces']) && 
                   in_array($type, $service['metadata']['interfaces']);
        });
    }

    /**
     * Find services by method name
     *
     * @param string $methodName
     * @return Collection
     */
    public function findByMethod(string $methodName): Collection
    {
        return $this->services->filter(function ($service) use ($methodName) {
            return isset($service['methods']) && 
                   in_array($methodName, array_column($service['methods'], 'name'));
        });
    }

    /**
     * Get all registered services
     *
     * @return Collection
     */
    public function getAll(): Collection
    {
        return $this->services;
    }

    /**
     * Clear all registered services
     */
    public function clear(): void
    {
        $this->services = new Collection();
        $this->saveToCache();
    }

    /**
     * Validate a service
     *
     * @param array $service
     * @return bool
     */
    protected function validateService(array $service): bool
    {
        return isset($service['class']) && 
               isset($service['methods']) && 
               isset($service['metadata']);
    }

    /**
     * Load services from cache
     */
    protected function loadFromCache(): void
    {
        $cachedServices = Cache::get($this->cacheKey);

        if ($cachedServices) {
            $this->services = new Collection($cachedServices);
        }
    }

    /**
     * Save services to cache
     */
    protected function saveToCache(): void
    {
        Cache::put($this->cacheKey, $this->services->toArray(), $this->cacheTtl);
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