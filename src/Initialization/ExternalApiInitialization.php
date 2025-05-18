<?php

namespace LegalStudy\Initialization;

use GuzzleHttp\Client;
use GuzzleHttp\HandlerStack;
use GuzzleHttp\Middleware;

class ExternalApiInitialization extends AbstractInitialization
{
    private ?Client $client = null;

    protected function doValidateConfiguration(): bool
    {
        if (!isset($this->config['base_url'])) {
            $this->addError('API base URL is required');
            return false;
        }

        if (!filter_var($this->config['base_url'], FILTER_VALIDATE_URL)) {
            $this->addError('Invalid API base URL');
            return false;
        }

        return true;
    }

    protected function createClient(array $config): Client
    {
        $stack = HandlerStack::create();
            
        // Add retry middleware
        $stack->push(Middleware::retry(
            function ($retries, $request, $response, $exception) {
                return $retries < ($this->config['retries'] ?? 3) &&
                    ($response && ($response->getStatusCode() === 429 || $response->getStatusCode() >= 500));
            },
            function ($retries) {
                return 1000 * pow(2, $retries);
            }
        ));

        return new Client([
            'base_uri' => $config['base_url'],
            'timeout' => $config['timeout'] ?? 30,
            'headers' => $config['headers'] ?? [],
            'handler' => $stack,
            'http_errors' => false
        ]);
    }

    protected function doTestConnection(): bool
    {
        try {
            $this->client = $this->createClient($this->config);
            $response = $this->client->get('/');
            
            if ($response->getStatusCode() >= 500) {
                $this->addError('API server error: ' . $response->getStatusCode());
                return false;
            }

            if ($response->getStatusCode() >= 400) {
                $this->addError('API client error: ' . $response->getStatusCode());
                return false;
            }

            return true;
        } catch (\Exception $e) {
            $this->addError('API connection test failed: ' . $e->getMessage());
            return false;
        }
    }

    protected function doPerformInitialization(): void
    {
        try {
            if (!$this->client) {
                $this->client = $this->createClient($this->config);
            }

            // Test the connection
            $response = $this->client->get('/');
            
            if ($response->getStatusCode() >= 500) {
                throw new \RuntimeException('API server error: ' . $response->getStatusCode());
            }

            $this->addData('connected', true);
            $this->addData('status_code', $response->getStatusCode());
        } catch (\Exception $e) {
            $this->client = null;
            throw new \RuntimeException('API initialization failed: ' . $e->getMessage());
        }
    }

    public function getClient(): ?Client
    {
        return $this->client;
    }

    public function __destruct()
    {
        $this->client = null;
    }
} 