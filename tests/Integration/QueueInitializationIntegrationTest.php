<?php

namespace LegalStudy\ModularInitialization\Tests\Integration;

use LegalStudy\ModularInitialization\Initializers\QueueInitialization;
use LegalStudy\ModularInitialization\Services\InitializationStatus;
use PHPUnit\Framework\TestCase;

class QueueInitializationIntegrationTest extends TestCase
{
    private QueueInitialization $initialization;
    private InitializationStatus $status;
    private array $config;

    protected function setUp(): void
    {
        $this->status = new InitializationStatus();
        $this->initialization = new QueueInitialization($this->status);
        
        $this->config = [
            'host' => getenv('QUEUE_HOST') ?: 'localhost',
            'port' => (int)(getenv('QUEUE_PORT') ?: 5672),
            'user' => getenv('QUEUE_USER') ?: 'guest',
            'password' => getenv('QUEUE_PASS') ?: 'guest',
            'vhost' => getenv('QUEUE_VHOST') ?: '/'
        ];
    }

    public function testQueueInitialization(): void
    {
        $this->assertTrue($this->initialization->validateConfiguration($this->config));
        $this->initialization->performInitialization();

        $this->assertTrue($this->status->isInitialized());
        $this->assertEmpty($this->status->getErrors());
        
        $data = $this->status->getData('connected');
        $this->assertTrue($data);
        
        $properties = $this->status->getData('server_properties');
        $this->assertIsArray($properties);
    }

    public function testConnectionValidation(): void
    {
        $this->initialization->validateConfiguration($this->config);
        $this->assertTrue($this->initialization->testConnection());
    }

    public function testErrorHandling(): void
    {
        $invalidConfig = array_merge($this->config, [
            'host' => 'invalid-host',
            'port' => 9999
        ]);

        $this->initialization->validateConfiguration($invalidConfig);
        $this->initialization->performInitialization();

        $this->assertTrue($this->status->isFailed());
        $this->assertNotEmpty($this->status->getErrors());
    }

    public function testChannelOperations(): void
    {
        $this->initialization->validateConfiguration($this->config);
        $this->initialization->performInitialization();

        $channel = $this->initialization->getChannel();
        $this->assertNotNull($channel);
        $this->assertTrue($channel->is_open());

        // Test queue declaration
        $channel->queue_declare('test_queue', false, true, false, false);
        
        // Test message publishing
        $channel->basic_publish(
            new \PhpAmqpLib\Message\AMQPMessage('test message'),
            '',
            'test_queue'
        );

        // Test message consumption
        $received = false;
        $channel->basic_consume(
            'test_queue',
            '',
            false,
            true,
            false,
            false,
            function () use (&$received) {
                $received = true;
            }
        );

        $channel->wait(null, false, 1);
        $this->assertTrue($received);
    }

    protected function tearDown(): void
    {
        if ($this->status->isInitialized()) {
            $channel = $this->initialization->getChannel();
            if ($channel !== null) {
                $channel->close();
            }
            
            $connection = $this->initialization->getConnection();
            if ($connection !== null) {
                $connection->close();
            }
        }
    }
} 