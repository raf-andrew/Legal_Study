<?php

namespace LegalStudy\ModularInitialization\Tests\Integration;

use LegalStudy\ModularInitialization\Initializers\NetworkInitialization;
use LegalStudy\ModularInitialization\Services\InitializationStatus;
use PHPUnit\Framework\TestCase;

class NetworkInitializationIntegrationTest extends TestCase
{
    private NetworkInitialization $initialization;
    private InitializationStatus $status;
    private array $config;

    protected function setUp(): void
    {
        $this->status = new InitializationStatus();
        $this->initialization = new NetworkInitialization($this->status);
        
        $this->config = [
            'connections' => [
                'database' => [
                    'host' => getenv('DB_HOST') ?: 'localhost',
                    'port' => (int)(getenv('DB_PORT') ?: 3306),
                    'timeout' => 5
                ],
                'cache' => [
                    'host' => getenv('CACHE_HOST') ?: 'localhost',
                    'port' => (int)(getenv('CACHE_PORT') ?: 6379),
                    'timeout' => 5
                ],
                'queue' => [
                    'host' => getenv('QUEUE_HOST') ?: 'localhost',
                    'port' => (int)(getenv('QUEUE_PORT') ?: 5672),
                    'timeout' => 5
                ]
            ]
        ];
    }

    public function testNetworkInitialization(): void
    {
        $this->assertTrue($this->initialization->validateConfiguration($this->config));
        $this->initialization->performInitialization();

        $this->assertTrue($this->status->isInitialized());
        $this->assertEmpty($this->status->getErrors());
    }

    public function testConnectionValidation(): void
    {
        $this->initialization->validateConfiguration($this->config);
        $this->assertTrue($this->initialization->validateConnections());
    }

    public function testPortValidation(): void
    {
        $this->initialization->validateConfiguration($this->config);
        $this->assertTrue($this->initialization->validatePorts());
    }

    public function testConnectionTesting(): void
    {
        $this->initialization->validateConfiguration($this->config);
        $this->assertTrue($this->initialization->testConnection());
    }

    public function testErrorHandling(): void
    {
        $invalidConfig = array_merge($this->config, [
            'connections' => [
                'database' => [
                    'host' => 'invalid-host',
                    'port' => 9999,
                    'timeout' => 1
                ]
            ]
        ]);

        $this->initialization->validateConfiguration($invalidConfig);
        $this->initialization->performInitialization();

        $this->assertTrue($this->status->isFailed());
        $this->assertNotEmpty($this->status->getErrors());
    }

    public function testTimeoutHandling(): void
    {
        $timeoutConfig = array_merge($this->config, [
            'connections' => [
                'database' => [
                    'host' => 'localhost',
                    'port' => 3306,
                    'timeout' => 1 // Very short timeout
                ]
            ]
        ]);

        $this->initialization->validateConfiguration($timeoutConfig);
        $this->initialization->performInitialization();

        $this->assertTrue($this->status->isFailed());
        $this->assertNotEmpty($this->status->getErrors());
    }

    protected function tearDown(): void
    {
        if ($this->status->isInitialized()) {
            // Close any open connections
            $this->initialization->closeConnections();
        }
    }
} 