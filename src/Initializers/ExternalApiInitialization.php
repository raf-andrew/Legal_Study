<?php

namespace LegalStudy\ModularInitialization\Initializers;

use GuzzleHttp\Client;
use GuzzleHttp\Handler\MockHandler;
use GuzzleHttp\HandlerStack;
use GuzzleHttp\Psr7\Response;
use LegalStudy\ModularInitialization\AbstractInitialization;
use LegalStudy\ModularInitialization\Services\InitializationStatus;

class ExternalApiInitialization extends AbstractInitialization
{
    private ?Client $client = null;
    private ?MockHandler $mockHandler = null;
    private int $maxRetries = 3;
    private int $timeout = 30;

    public function __construct(?MockHandler $mockHandler = null)
    {
        $this->mockHandler = $mockHandler;
    }

    protected function doValidateConfiguration(): void
    {
        $requiredKeys = ['base_uri', 'api_key'];
        foreach ($requiredKeys as $key) {
            if (!isset($this->config[$key])) {
                $this->addError("Missing required configuration key: {$key}");
            }
        }

        if (isset($this->config['base_uri']) && !filter_var($this->config['base_uri'], FILTER_VALIDATE_URL)) {
            $this->addError("Invalid base_uri format");
        }

        if (isset($this->config['api_key']) && empty($this->config['api_key'])) {
            $this->addError("API key cannot be empty");
        }
    }

    protected function doTestConnection(): bool
    {
        try {
            $client = $this->getClient();
            $response = $client->get('/health');
            
            if ($response->getStatusCode() !== 200) {
                $this->addError("Health check failed with status: " . $response->getStatusCode());
                return false;
            }

            return true;
        } catch (\Exception $e) {
            $this->addError("Connection test failed: " . $e->getMessage());
            return false;
        }
    }

    protected function doPerformInitialization(): void
    {
        try {
            $this->initializeEndpoints();
            $this->testApiFunctionality();
        } catch (\Exception $e) {
            $this->addError("Initialization failed: " . $e->getMessage());
            throw $e;
        }
    }

    private function getClient(): Client
    {
        if ($this->client === null) {
            $config = [
                'base_uri' => $this->config['base_uri'],
                'timeout' => $this->timeout,
                'headers' => [
                    'Authorization' => 'Bearer ' . $this->config['api_key'],
                    'Accept' => 'application/json',
                ],
            ];

            if ($this->mockHandler !== null) {
                $handlerStack = HandlerStack::create($this->mockHandler);
                $config['handler'] = $handlerStack;
            }

            $this->client = new Client($config);
        }

        return $this->client;
    }

    private function initializeEndpoints(): void
    {
        // Initialize API endpoints here
        // This is a placeholder for actual endpoint initialization logic
    }

    private function testApiFunctionality(): void
    {
        // Test API functionality here
        // This is a placeholder for actual API testing logic
    }

    public function getClientInstance(): Client
    {
        return $this->getClient();
    }
} 