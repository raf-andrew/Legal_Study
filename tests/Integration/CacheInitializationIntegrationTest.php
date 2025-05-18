<?php

namespace Tests\Integration;

use LegalStudy\ModularInitialization\Initializers\CacheInitialization;
use LegalStudy\ModularInitialization\Services\InitializationStatus;
use PHPUnit\Framework\TestCase;

class CacheInitializationIntegrationTest extends TestCase
{
    private CacheInitialization $initialization;
    private array $config;

    protected function setUp(): void
    {
        $this->config = [
            'driver' => 'redis',
            'connection' => [
                'host' => getenv('CACHE_HOST') ?: 'localhost',
                'port' => (int)(getenv('CACHE_PORT') ?: 6379),
                'password' => getenv('CACHE_PASS') ?: null,
                'database' => (int)(getenv('CACHE_DB') ?: 0)
            ]
        ];

        $this->initialization = new CacheInitialization(new InitializationStatus());
    }

    public function testCacheConnection(): void
    {
        $this->assertTrue($this->initialization->validateConfiguration($this->config));
        $this->assertTrue($this->initialization->testConnection());
    }

    public function testCacheInitialization(): void
    {
        $this->initialization->validateConfiguration($this->config);
        $this->initialization->performInitialization();

        $status = $this->initialization->getStatus();
        $this->assertTrue($status->isInitialized());
        $this->assertEmpty($status->getErrors());
    }

    public function testCacheOperations(): void
    {
        $this->initialization->validateConfiguration($this->config);
        $this->initialization->performInitialization();

        $client = $this->initialization->getClient();
        
        // Test set
        $client->set('test_key', 'test_value');
        
        // Test get
        $value = $client->get('test_key');
        $this->assertEquals('test_value', $value);
        
        // Test delete
        $client->del('test_key');
        $this->assertFalse($client->get('test_key'));
    }

    public function testErrorHandling(): void
    {
        $invalidConfig = array_merge($this->config, [
            'connection' => [
                'host' => 'localhost',
                'port' => 9999 // Invalid port
            ]
        ]);

        $this->initialization->validateConfiguration($invalidConfig);
        $this->initialization->performInitialization();

        $status = $this->initialization->getStatus();
        $this->assertTrue($status->isFailed());
        $this->assertNotEmpty($status->getErrors());
    }

    protected function tearDown(): void
    {
        if ($this->initialization->getStatus()->isInitialized()) {
            $client = $this->initialization->getClient();
            $client->flushDB();
        }
    }
} 