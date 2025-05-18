<?php

namespace LegalStudy\ModularInitialization\Tests\Initialization;

use LegalStudy\ModularInitialization\Initializers\CacheInitialization;
use LegalStudy\ModularInitialization\Services\InitializationStatus;
use PHPUnit\Framework\TestCase;
use Predis\Client;
use Predis\Connection\ConnectionException;
use Predis\Connection\NodeConnectionInterface;

/**
 * @covers \LegalStudy\ModularInitialization\Initializers\CacheInitialization
 * @covers \LegalStudy\ModularInitialization\AbstractInitialization
 * @covers \LegalStudy\ModularInitialization\Services\InitializationStatus
 */
class CacheInitializationTest extends TestCase
{
    protected CacheInitialization $cache;
    protected InitializationStatus $status;

    protected function setUp(): void
    {
        $this->status = new InitializationStatus();
        $this->cache = new CacheInitialization($this->status);
    }

    public function test_validate_configuration_with_missing_driver(): void
    {
        $config = [
            'connection' => [
                'host' => 'localhost',
                'port' => 6379
            ]
        ];
        
        $this->expectException(\InvalidArgumentException::class);
        $this->expectExceptionMessage('Cache driver must be specified');
        
        $this->cache->validateConfiguration($config);
    }

    public function test_validate_configuration_with_missing_connection(): void
    {
        $config = [
            'driver' => 'redis'
        ];
        
        $this->expectException(\InvalidArgumentException::class);
        $this->expectExceptionMessage('Cache connection settings must be specified');
        
        $this->cache->validateConfiguration($config);
    }

    public function test_validate_configuration_with_invalid_connection(): void
    {
        $config = [
            'driver' => 'redis',
            'connection' => 'invalid'
        ];
        
        $this->expectException(\InvalidArgumentException::class);
        $this->expectExceptionMessage('Cache connection settings must be an array');
        
        $this->cache->validateConfiguration($config);
    }

    public function test_validate_configuration_with_missing_host(): void
    {
        $config = [
            'driver' => 'redis',
            'connection' => [
                'port' => 6379
            ]
        ];
        
        $this->expectException(\InvalidArgumentException::class);
        $this->expectExceptionMessage('Cache connection host must be specified');
        
        $this->cache->validateConfiguration($config);
    }

    public function test_validate_configuration_with_missing_port(): void
    {
        $config = [
            'driver' => 'redis',
            'connection' => [
                'host' => 'localhost'
            ]
        ];
        
        $this->expectException(\InvalidArgumentException::class);
        $this->expectExceptionMessage('Cache connection port must be specified');
        
        $this->cache->validateConfiguration($config);
    }

    public function test_validate_configuration_with_valid_config(): void
    {
        $config = [
            'driver' => 'redis',
            'connection' => [
                'host' => 'localhost',
                'port' => 6379
            ]
        ];
        
        $this->assertTrue($this->cache->validateConfiguration($config));
        $this->assertEmpty($this->status->getErrors());
        $this->assertFalse($this->status->isFailed());
    }

    public function test_validate_configuration_with_password(): void
    {
        $config = [
            'driver' => 'redis',
            'connection' => [
                'host' => 'localhost',
                'port' => 6379,
                'password' => 'secret'
            ]
        ];
        
        $this->assertTrue($this->cache->validateConfiguration($config));
        $this->assertEmpty($this->status->getErrors());
        $this->assertFalse($this->status->isFailed());
    }

    public function test_validate_configuration_with_database(): void
    {
        $config = [
            'driver' => 'redis',
            'connection' => [
                'host' => 'localhost',
                'port' => 6379,
                'database' => 1
            ]
        ];
        
        $this->assertTrue($this->cache->validateConfiguration($config));
        $this->assertEmpty($this->status->getErrors());
        $this->assertFalse($this->status->isFailed());
    }

    public function test_validate_configuration_with_invalid_database(): void
    {
        $config = [
            'driver' => 'redis',
            'connection' => [
                'host' => 'localhost',
                'port' => 6379,
                'database' => 'invalid'
            ]
        ];
        
        $this->expectException(\InvalidArgumentException::class);
        $this->expectExceptionMessage('Cache connection database must be an integer');
        
        $this->cache->validateConfiguration($config);
    }

    public function test_test_connection_with_mock_client(): void
    {
        $config = [
            'driver' => 'redis',
            'connection' => [
                'host' => 'localhost',
                'port' => 6379
            ]
        ];

        $mockClient = $this->getMockBuilder(Client::class)
            ->disableOriginalConstructor()
            ->onlyMethods(['__call'])
            ->getMock();

        $mockClient->expects($this->once())
            ->method('__call')
            ->with('ping')
            ->willReturn('PONG');

        $this->cache->setConfig($config);
        $this->cache->setClient($mockClient);

        $this->assertTrue($this->cache->testConnection());
        $this->assertEmpty($this->status->getErrors());
        $this->assertFalse($this->status->isFailed());
    }

    public function test_test_connection_with_mock_client_failure(): void
    {
        $config = [
            'driver' => 'redis',
            'connection' => [
                'host' => 'localhost',
                'port' => 6379
            ]
        ];

        $mockConnection = $this->createMock(NodeConnectionInterface::class);
        $mockClient = $this->getMockBuilder(Client::class)
            ->disableOriginalConstructor()
            ->onlyMethods(['__call'])
            ->getMock();

        $mockClient->expects($this->once())
            ->method('__call')
            ->with('ping')
            ->willThrowException(new ConnectionException($mockConnection, 'Connection failed'));

        $this->cache->setConfig($config);
        $this->cache->setClient($mockClient);

        $this->expectException(\RuntimeException::class);
        $this->expectExceptionMessage('Cache connection test failed: Connection failed');

        $this->cache->testConnection();
    }

    public function test_perform_initialization_with_mock_client(): void
    {
        $config = [
            'driver' => 'redis',
            'connection' => [
                'host' => 'localhost',
                'port' => 6379
            ]
        ];

        $mockClient = $this->getMockBuilder(Client::class)
            ->disableOriginalConstructor()
            ->onlyMethods(['__call'])
            ->getMock();

        $mockClient->expects($this->once())
            ->method('__call')
            ->with('flushall')
            ->willReturn(true);

        $this->cache->setConfig($config);
        $this->cache->setClient($mockClient);

        $this->assertTrue($this->cache->performInitialization());
        $this->assertTrue($this->status->isInitialized());
        $this->assertEmpty($this->status->getErrors());
        $this->assertFalse($this->status->isFailed());
    }

    public function test_perform_initialization_with_mock_client_failure(): void
    {
        $config = [
            'driver' => 'redis',
            'connection' => [
                'host' => 'localhost',
                'port' => 6379
            ]
        ];

        $mockConnection = $this->createMock(NodeConnectionInterface::class);
        $mockClient = $this->getMockBuilder(Client::class)
            ->disableOriginalConstructor()
            ->onlyMethods(['__call'])
            ->getMock();

        $mockClient->expects($this->once())
            ->method('__call')
            ->with('flushall')
            ->willThrowException(new ConnectionException($mockConnection, 'Connection failed'));

        $this->cache->setConfig($config);
        $this->cache->setClient($mockClient);

        $this->expectException(\RuntimeException::class);
        $this->expectExceptionMessage('Cache initialization failed: Connection failed');

        $this->cache->performInitialization();
    }

    public function test_test_connection_with_timeout(): void
    {
        $config = [
            'driver' => 'redis',
            'connection' => [
                'host' => 'localhost',
                'port' => 6379,
                'timeout' => 0.5
            ]
        ];

        $mockConnection = $this->createMock(NodeConnectionInterface::class);
        $mockClient = $this->getMockBuilder(Client::class)
            ->disableOriginalConstructor()
            ->onlyMethods(['__call'])
            ->getMock();

        $mockClient->expects($this->once())
            ->method('__call')
            ->with('ping')
            ->willThrowException(new ConnectionException($mockConnection, 'Connection timed out'));

        $this->cache->setConfig($config);
        $this->cache->setClient($mockClient);

        $this->expectException(\RuntimeException::class);
        $this->expectExceptionMessage('Cache connection test failed: Connection timed out');

        $this->cache->testConnection();
    }

    public function test_test_connection_with_retry(): void
    {
        $config = [
            'driver' => 'redis',
            'connection' => [
                'host' => 'localhost',
                'port' => 6379,
                'retry_attempts' => 3,
                'retry_delay' => 0.1
            ]
        ];

        $mockConnection = $this->createMock(NodeConnectionInterface::class);
        $mockClient = $this->getMockBuilder(Client::class)
            ->disableOriginalConstructor()
            ->onlyMethods(['__call'])
            ->getMock();

        $mockClient->expects($this->exactly(3))
            ->method('__call')
            ->with('ping')
            ->willThrowException(new ConnectionException($mockConnection, 'Connection failed'));

        $this->cache->setConfig($config);
        $this->cache->setClient($mockClient);

        $this->expectException(\RuntimeException::class);
        $this->expectExceptionMessage('Cache connection test failed: Connection failed');

        $this->cache->testConnection();
    }
} 