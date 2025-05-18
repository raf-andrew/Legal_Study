<?php

namespace LegalStudy\Initialization;

use Predis\Client;
use RuntimeException;

class CacheInitialization extends AbstractInitialization
{
    private ?Client $client = null;

    protected function doValidateConfiguration(): bool
    {
        if (!isset($this->config['host'])) {
            $this->addError('Cache host is required');
            return false;
        }

        if (!isset($this->config['port'])) {
            $this->addError('Cache port is required');
            return false;
        }

        return true;
    }

    protected function doTestConnection(): bool
    {
        try {
            $options = ['timeout' => $this->config['timeout'] ?? 2.0];
            if (isset($this->config['password'])) {
                $options['password'] = $this->config['password'];
            }
            if (isset($this->config['database'])) {
                $options['database'] = $this->config['database'];
            }

            $client = $this->createClient([
                'scheme' => 'tcp',
                'host' => $this->config['host'],
                'port' => $this->config['port']
            ], $options);

            // Test connection by sending a PING command
            $response = $client->ping();
            if ($response !== 'PONG') {
                $this->addError('Failed to connect to Redis server');
                return false;
            }

            $client->quit();
            return true;
        } catch (\Exception $e) {
            $this->addError('Connection test failed: ' . $e->getMessage());
            return false;
        }
    }

    protected function doPerformInitialization(): void
    {
        try {
            $options = ['timeout' => $this->config['timeout'] ?? 2.0];
            if (isset($this->config['password'])) {
                $options['password'] = $this->config['password'];
            }
            if (isset($this->config['database'])) {
                $options['database'] = $this->config['database'];
            }

            $this->client = $this->createClient([
                'scheme' => 'tcp',
                'host' => $this->config['host'],
                'port' => $this->config['port']
            ], $options);

            // Test connection
            $response = $this->client->ping();
            if ($response !== 'PONG') {
                throw new RuntimeException('Failed to connect to Redis server');
            }

            $this->addData('connected', true);
            $info = $this->client->info();
            $this->addData('version', $info['Server']['redis_version']);
            $this->markComplete();
        } catch (\Exception $e) {
            $this->client = null;
            throw new RuntimeException('Cache initialization failed: ' . $e->getMessage());
        }
    }

    protected function createClient(array $parameters, array $options): Client
    {
        return new Client($parameters, $options);
    }

    public function getClient(): ?Client
    {
        return $this->client;
    }

    public function __destruct()
    {
        if ($this->client !== null) {
            $this->client->quit();
        }
    }
} 