<?php

namespace LegalStudy\ModularInitialization\Initializers;

use Predis\Client;
use Predis\Connection\ConnectionException;
use LegalStudy\ModularInitialization\AbstractInitialization;
use LegalStudy\ModularInitialization\Services\InitializationStatus;

class CacheInitialization extends AbstractInitialization
{
    private ?Client $client = null;
    private int $maxRetries = 3;
    private int $timeout = 30;

    protected function doValidateConfiguration(): void
    {
        $requiredKeys = ['host', 'port', 'database'];
        foreach ($requiredKeys as $key) {
            if (!isset($this->config[$key])) {
                $this->addError("Missing required configuration key: {$key}");
            }
        }

        if (isset($this->config['port']) && (!is_numeric($this->config['port']) || $this->config['port'] <= 0)) {
            $this->addError("Invalid port value");
        }

        if (isset($this->config['timeout']) && (!is_numeric($this->config['timeout']) || $this->config['timeout'] <= 0)) {
            $this->addError("Invalid timeout value");
        }

        if (isset($this->config['max_retries']) && (!is_numeric($this->config['max_retries']) || $this->config['max_retries'] < 0)) {
            $this->addError("Invalid max_retries value");
        }
    }

    protected function doTestConnection(): bool
    {
        try {
            $client = $this->getClient();
            
            // Test the connection with a simple command
            $client->ping();
            
            return true;
        } catch (ConnectionException $e) {
            $this->addError("Connection test failed: " . $e->getMessage());
            return false;
        }
    }

    protected function doPerformInitialization(): void
    {
        try {
            $client = $this->getClient();
            
            // Test basic cache operations
            $testKey = 'test_' . uniqid();
            $testValue = 'test_value';
            
            // Test set
            $client->set($testKey, $testValue);
            
            // Test get
            $retrievedValue = $client->get($testKey);
            if ($retrievedValue !== $testValue) {
                throw new \RuntimeException("Cache get operation failed");
            }
            
            // Test delete
            $client->del($testKey);
            
            // Verify deletion
            if ($client->exists($testKey)) {
                throw new \RuntimeException("Cache delete operation failed");
            }
        } catch (\Exception $e) {
            $this->addError("Initialization failed: " . $e->getMessage());
            throw $e;
        }
    }

    private function getClient(): Client
    {
        if ($this->client === null) {
            $parameters = [
                'host' => $this->config['host'],
                'port' => $this->config['port'],
                'database' => $this->config['database'],
                'timeout' => $this->timeout
            ];

            $options = [
                'parameters' => [
                    'password' => $this->config['password'] ?? null,
                    'database' => $this->config['database']
                ]
            ];

            $this->client = new Client($parameters, $options);
        }

        return $this->client;
    }

    public function getClientInstance(): Client
    {
        return $this->getClient();
    }
} 