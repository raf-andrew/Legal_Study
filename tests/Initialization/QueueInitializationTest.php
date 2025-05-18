<?php

namespace Tests\Initialization;

use LegalStudy\ModularInitialization\Initializers\QueueInitialization;
use PHPUnit\Framework\TestCase;

class QueueInitializationTest extends TestCase
{
    private QueueInitialization $initialization;

    protected function setUp(): void
    {
        $this->initialization = new QueueInitialization();
    }

    public function testValidateConfiguration(): void
    {
        $validConfig = [
            'host' => 'localhost',
            'port' => 5672,
            'username' => 'test_user',
            'password' => 'test_pass',
            'vhost' => '/'
        ];

        $this->assertTrue($this->initialization->validateConfiguration($validConfig));

        $invalidConfig = [
            'host' => 'localhost',
            'port' => 5672
        ];

        $this->expectException(\InvalidArgumentException::class);
        $this->initialization->validateConfiguration($invalidConfig);
    }

    public function testTestConnection(): void
    {
        $config = [
            'host' => 'localhost',
            'port' => 5672,
            'username' => 'test_user',
            'password' => 'test_pass',
            'vhost' => '/'
        ];

        $this->initialization->validateConfiguration($config);
        
        // Mock AMQP connection
        $connectionMock = $this->createMock(\AMQPConnection::class);
        $connectionMock->method('isConnected')->willReturn(true);
        
        $reflection = new \ReflectionClass($this->initialization);
        $property = $reflection->getProperty('connection');
        $property->setAccessible(true);
        $property->setValue($this->initialization, $connectionMock);

        $this->assertTrue($this->initialization->testConnection());
    }

    public function testPerformInitialization(): void
    {
        $config = [
            'host' => 'localhost',
            'port' => 5672,
            'username' => 'test_user',
            'password' => 'test_pass',
            'vhost' => '/'
        ];

        $this->initialization->validateConfiguration($config);
        
        // Mock AMQP connection and channel
        $connectionMock = $this->createMock(\AMQPConnection::class);
        $connectionMock->method('isConnected')->willReturn(true);
        
        $channelMock = $this->createMock(\AMQPChannel::class);
        $channelMock->method('isConnected')->willReturn(true);
        
        $reflection = new \ReflectionClass($this->initialization);
        $connectionProperty = $reflection->getProperty('connection');
        $connectionProperty->setAccessible(true);
        $connectionProperty->setValue($this->initialization, $connectionMock);
        
        $channelProperty = $reflection->getProperty('channel');
        $channelProperty->setAccessible(true);
        $channelProperty->setValue($this->initialization, $channelMock);

        $this->initialization->performInitialization();
        $this->assertTrue($this->initialization->getStatus()->isInitialized());
    }

    public function testErrorHandling(): void
    {
        $config = [
            'host' => 'localhost',
            'port' => 5672,
            'username' => 'test_user',
            'password' => 'test_pass',
            'vhost' => '/'
        ];

        $this->initialization->validateConfiguration($config);
        
        // Mock AMQP connection that throws an exception
        $connectionMock = $this->createMock(\AMQPConnection::class);
        $connectionMock->method('isConnected')->willThrowException(new \AMQPConnectionException('Connection failed'));
        
        $reflection = new \ReflectionClass($this->initialization);
        $property = $reflection->getProperty('connection');
        $property->setAccessible(true);
        $property->setValue($this->initialization, $connectionMock);

        $this->initialization->performInitialization();
        $this->assertTrue($this->initialization->getStatus()->isFailed());
        $this->assertNotEmpty($this->initialization->getStatus()->getErrors());
    }
} 