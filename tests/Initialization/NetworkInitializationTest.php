<?php

namespace LegalStudy\ModularInitialization\Tests\Initialization;

use LegalStudy\ModularInitialization\Initializers\NetworkInitialization;
use LegalStudy\ModularInitialization\Services\InitializationStatus;
use PHPUnit\Framework\TestCase;
use InvalidArgumentException;
use RuntimeException;

/**
 * @covers \LegalStudy\ModularInitialization\Initializers\NetworkInitialization
 * @covers \LegalStudy\ModularInitialization\AbstractInitialization
 * @covers \LegalStudy\ModularInitialization\Services\InitializationStatus
 */
class NetworkInitializationTest extends TestCase
{
    private NetworkInitialization $initialization;
    private InitializationStatus $status;

    protected function setUp(): void
    {
        $this->status = new InitializationStatus();
        $this->initialization = new NetworkInitialization($this->status);
    }

    public function testValidateConfiguration(): void
    {
        $validConfig = [
            'connections' => [
                'database' => [
                    'host' => '127.0.0.1',
                    'port' => 3306,
                    'timeout' => 5
                ],
                'cache' => [
                    'host' => '127.0.0.1',
                    'port' => 6379,
                    'timeout' => 5
                ]
            ]
        ];

        $this->assertTrue($this->initialization->validateConfiguration($validConfig));

        // Test missing connections array
        $this->expectException(InvalidArgumentException::class);
        $this->expectExceptionMessage('Configuration must contain a connections array');
        $this->initialization->validateConfiguration([]);

        // Test missing host
        $this->expectException(InvalidArgumentException::class);
        $this->expectExceptionMessage('Host is required for connection: database');
        $this->initialization->validateConfiguration([
            'connections' => [
                'database' => [
                    'port' => 3306,
                    'timeout' => 5
                ]
            ]
        ]);

        // Test invalid port
        $this->expectException(InvalidArgumentException::class);
        $this->expectExceptionMessage('Invalid port for connection: database');
        $this->initialization->validateConfiguration([
            'connections' => [
                'database' => [
                    'host' => '127.0.0.1',
                    'port' => -1,
                    'timeout' => 5
                ]
            ]
        ]);
    }

    public function testTestConnection(): void
    {
        $config = [
            'connections' => [
                'database' => [
                    'host' => 'localhost',
                    'port' => 3306,
                    'timeout' => 5
                ]
            ]
        ];

        $this->initialization->validateConfiguration($config);
        $this->assertTrue($this->initialization->testConnection());
    }

    public function testPerformInitialization(): void
    {
        $config = [
            'connections' => [
                'database' => [
                    'host' => 'localhost',
                    'port' => 3306,
                    'timeout' => 5
                ],
                'cache' => [
                    'host' => '127.0.0.1',
                    'port' => 6379,
                    'timeout' => 2
                ]
            ]
        ];

        $this->initialization->validateConfiguration($config);
        $this->initialization->performInitialization();

        $this->assertTrue($this->status->isInitialized());
        
        $dbData = $this->status->getData('connection_database');
        $this->assertNotNull($dbData);
        $this->assertEquals('localhost', $dbData['host']);
        $this->assertEquals(3306, $dbData['port']);
        $this->assertTrue($dbData['connected']);

        $cacheData = $this->status->getData('connection_cache');
        $this->assertNotNull($cacheData);
        $this->assertEquals('127.0.0.1', $cacheData['host']);
        $this->assertEquals(6379, $cacheData['port']);
        $this->assertTrue($cacheData['connected']);
    }

    public function testErrorHandling(): void
    {
        $config = [
            'connections' => [
                'database' => [
                    'host' => 'invalid-host',
                    'port' => 3306,
                    'timeout' => 1
                ]
            ]
        ];

        $this->initialization->validateConfiguration($config);

        try {
            $this->initialization->performInitialization();
            $this->fail('Expected RuntimeException was not thrown');
        } catch (RuntimeException $e) {
            $this->assertStringContainsString('Failed to establish required network connections', $e->getMessage());
            $this->assertFalse($this->status->isInitialized());
            
            $connections = $this->initialization->getConnections();
            $this->assertArrayHasKey('database', $connections);
            $this->assertFalse($connections['database']['connected']);
            $this->assertArrayHasKey('error', $connections['database']);
        }
    }

    public function testValidatePorts(): void
    {
        $config = [
            'connections' => [
                'database' => [
                    'host' => 'localhost',
                    'port' => 3306,
                    'timeout' => 5
                ],
                'cache' => [
                    'host' => 'localhost',
                    'port' => 6379,
                    'timeout' => 2
                ]
            ]
        ];

        $this->initialization->validateConfiguration($config);
        $this->assertTrue($this->initialization->validatePorts());

        // Test invalid port
        $config = [
            'connections' => [
                'database' => [
                    'host' => 'localhost',
                    'port' => 99999,
                    'timeout' => 5
                ]
            ]
        ];

        $this->initialization->setConfig($config);
        $this->assertFalse($this->initialization->validatePorts());
        $this->assertStringContainsString('Invalid port for connection: database', $this->status->getErrors()[0]);
    }
} 