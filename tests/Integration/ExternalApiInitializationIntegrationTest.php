<?php

namespace Tests\Integration;

use LegalStudy\ModularInitialization\Initializers\ExternalApiInitialization;
use PHPUnit\Framework\TestCase;

class ExternalApiInitializationIntegrationTest extends TestCase
{
    private ExternalApiInitialization $initialization;
    private array $config;

    protected function setUp(): void
    {
        $this->config = [
            'base_url' => getenv('API_BASE_URL') ?: 'https://api.example.com',
            'timeout' => (int)(getenv('API_TIMEOUT') ?: 30),
            'retries' => (int)(getenv('API_RETRIES') ?: 3),
            'headers' => [
                'Authorization' => 'Bearer ' . (getenv('API_TOKEN') ?: 'test_token'),
                'Content-Type' => 'application/json'
            ]
        ];

        $this->initialization = new ExternalApiInitialization();
    }

    public function testApiConnection(): void
    {
        $this->assertTrue($this->initialization->validateConfiguration($this->config));
        $this->assertTrue($this->initialization->testConnection());
    }

    public function testApiInitialization(): void
    {
        $this->initialization->validateConfiguration($this->config);
        $this->initialization->performInitialization();

        $status = $this->initialization->getStatus();
        $this->assertTrue($status->isInitialized());
        $this->assertEmpty($status->getErrors());
    }

    public function testApiOperations(): void
    {
        $this->initialization->validateConfiguration($this->config);
        $this->initialization->performInitialization();

        $client = $this->initialization->getClient();
        
        // Test GET request
        $response = $client->get('/test-endpoint');
        $this->assertEquals(200, $response->getStatusCode());
        
        // Test POST request
        $response = $client->post('/test-endpoint', [
            'json' => ['test' => 'data']
        ]);
        $this->assertEquals(201, $response->getStatusCode());
        
        // Test error handling
        $response = $client->get('/non-existent-endpoint');
        $this->assertEquals(404, $response->getStatusCode());
    }

    public function testErrorHandling(): void
    {
        $invalidConfig = array_merge($this->config, [
            'base_url' => 'invalid-url'
        ]);

        $this->initialization->validateConfiguration($invalidConfig);
        $this->initialization->performInitialization();

        $status = $this->initialization->getStatus();
        $this->assertTrue($status->isFailed());
        $this->assertNotEmpty($status->getErrors());
    }

    public function testRetryLogic(): void
    {
        $this->initialization->validateConfiguration($this->config);
        $this->initialization->performInitialization();

        $client = $this->initialization->getClient();
        
        // Test with a temporarily unavailable endpoint
        $response = $client->get('/unavailable-endpoint');
        $this->assertTrue(
            $response->getStatusCode() === 503 || 
            $response->getStatusCode() === 429
        );
    }

    protected function tearDown(): void
    {
        if ($this->initialization->getStatus()->isInitialized()) {
            $client = $this->initialization->getClient();
            // Close any open connections
            $client->close();
        }
    }
} 