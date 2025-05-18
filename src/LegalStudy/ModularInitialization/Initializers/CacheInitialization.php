<?php

namespace LegalStudy\ModularInitialization\Initializers;

use LegalStudy\ModularInitialization\AbstractInitialization;

class CacheInitialization extends AbstractInitialization
{
    private const SUPPORTED_DRIVERS = ['file', 'redis', 'memcached'];

    protected function doValidateConfiguration(): bool
    {
        if (!isset($this->config['driver'])) {
            $this->status->addError('Cache driver not configured');
            return false;
        }

        if (!in_array($this->config['driver'], self::SUPPORTED_DRIVERS)) {
            $this->status->addError('Unsupported cache driver');
            return false;
        }

        return true;
    }

    protected function doTestConnection(): bool
    {
        try {
            switch ($this->config['driver']) {
                case 'file':
                    return $this->testFileDriver();
                case 'redis':
                    return $this->testRedisDriver();
                case 'memcached':
                    return $this->testMemcachedDriver();
                default:
                    $this->status->addError('Invalid cache driver');
                    return false;
            }
        } catch (\Throwable $e) {
            $this->status->addError("Cache connection test failed: {$e->getMessage()}");
            return false;
        }
    }

    protected function doPerformInitialization(): void
    {
        try {
            switch ($this->config['driver']) {
                case 'file':
                    $this->initializeFileDriver();
                    break;
                case 'redis':
                    $this->initializeRedisDriver();
                    break;
                case 'memcached':
                    $this->initializeMemcachedDriver();
                    break;
                default:
                    throw new \RuntimeException('Invalid cache driver');
            }

            $this->status->setInitialized(true);
        } catch (\Throwable $e) {
            throw new \RuntimeException("Cache initialization failed: {$e->getMessage()}");
        }
    }

    private function testFileDriver(): bool
    {
        $path = $this->config['path'] ?? sys_get_temp_dir() . '/cache';
        
        if (!is_dir($path)) {
            if (!@mkdir($path, 0755, true)) {
                $this->status->addError('Could not create cache directory');
                return false;
            }
        }

        if (!is_writable($path)) {
            $this->status->addError('Cache directory is not writable');
            return false;
        }

        return true;
    }

    private function testRedisDriver(): bool
    {
        if (!extension_loaded('redis')) {
            $this->status->addError('Redis extension not installed');
            return false;
        }

        $redis = new \Redis();
        try {
            $redis->connect(
                $this->config['host'] ?? '127.0.0.1',
                $this->config['port'] ?? 6379,
                $this->config['timeout'] ?? 0.0
            );
            return true;
        } catch (\RedisException $e) {
            $this->status->addError("Redis connection failed: {$e->getMessage()}");
            return false;
        }
    }

    private function testMemcachedDriver(): bool
    {
        if (!extension_loaded('memcached')) {
            $this->status->addError('Memcached extension not installed');
            return false;
        }

        $memcached = new \Memcached();
        try {
            $memcached->addServer(
                $this->config['host'] ?? '127.0.0.1',
                $this->config['port'] ?? 11211
            );
            return $memcached->getStats() !== false;
        } catch (\Exception $e) {
            $this->status->addError("Memcached connection failed: {$e->getMessage()}");
            return false;
        }
    }

    private function initializeFileDriver(): void
    {
        $path = $this->config['path'] ?? sys_get_temp_dir() . '/cache';
        
        if (!is_dir($path)) {
            if (!@mkdir($path, 0755, true)) {
                throw new \RuntimeException('Could not create cache directory');
            }
        }

        if (!is_writable($path)) {
            throw new \RuntimeException('Cache directory is not writable');
        }

        // Create a test file to verify write permissions
        $testFile = $path . '/test.cache';
        if (!@file_put_contents($testFile, 'test')) {
            throw new \RuntimeException('Could not write to cache directory');
        }
        @unlink($testFile);
    }

    private function initializeRedisDriver(): void
    {
        if (!extension_loaded('redis')) {
            throw new \RuntimeException('Redis extension not installed');
        }

        $redis = new \Redis();
        try {
            $redis->connect(
                $this->config['host'] ?? '127.0.0.1',
                $this->config['port'] ?? 6379,
                $this->config['timeout'] ?? 0.0
            );

            if (isset($this->config['password'])) {
                $redis->auth($this->config['password']);
            }

            if (isset($this->config['database'])) {
                $redis->select($this->config['database']);
            }

            // Test connection with a ping
            if ($redis->ping() !== true) {
                throw new \RuntimeException('Redis ping failed');
            }
        } catch (\RedisException $e) {
            throw new \RuntimeException("Redis initialization failed: {$e->getMessage()}");
        }
    }

    private function initializeMemcachedDriver(): void
    {
        if (!extension_loaded('memcached')) {
            throw new \RuntimeException('Memcached extension not installed');
        }

        $memcached = new \Memcached();
        try {
            $memcached->addServer(
                $this->config['host'] ?? '127.0.0.1',
                $this->config['port'] ?? 11211
            );

            if ($memcached->getStats() === false) {
                throw new \RuntimeException('Could not connect to Memcached server');
            }

            // Test set/get operations
            if (!$memcached->set('test_key', 'test_value', 60)) {
                throw new \RuntimeException('Could not write to Memcached server');
            }

            if ($memcached->get('test_key') !== 'test_value') {
                throw new \RuntimeException('Could not read from Memcached server');
            }

            $memcached->delete('test_key');
        } catch (\Exception $e) {
            throw new \RuntimeException("Memcached initialization failed: {$e->getMessage()}");
        }
    }
} 