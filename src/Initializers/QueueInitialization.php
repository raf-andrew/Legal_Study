<?php

namespace LegalStudy\ModularInitialization\Initializers;

use PhpAmqpLib\Connection\AMQPStreamConnection;
use PhpAmqpLib\Message\AMQPMessage;
use LegalStudy\ModularInitialization\AbstractInitialization;
use LegalStudy\ModularInitialization\Services\InitializationStatus;

class QueueInitialization extends AbstractInitialization
{
    private ?AMQPStreamConnection $connection = null;
    private int $maxRetries = 3;
    private int $timeout = 30;

    protected function doValidateConfiguration(): void
    {
        $requiredKeys = ['host', 'port', 'user', 'password', 'vhost'];
        foreach ($requiredKeys as $key) {
            if (!isset($this->config[$key])) {
                $this->addError("Missing required configuration key: {$key}");
            }
        }

        if (isset($this->config['port']) && (!is_numeric($this->config['port']) || $this->config['port'] <= 0)) {
            $this->addError("Invalid port value");
        }

        if (isset($this->config['timeout']) && (!is_numeric($this->config['timeout']) || $this->config['timeout'] <= 0)) {
            $this->addError("Invalid timeout value");
        }

        if (isset($this->config['max_retries']) && (!is_numeric($this->config['max_retries']) || $this->config['max_retries'] < 0)) {
            $this->addError("Invalid max_retries value");
        }
    }

    protected function doTestConnection(): bool
    {
        try {
            $this->getConnection();
            return true;
        } catch (\Exception $e) {
            $this->addError("Connection test failed: " . $e->getMessage());
            return false;
        }
    }

    protected function doPerformInitialization(): void
    {
        try {
            $connection = $this->getConnection();
            $channel = $connection->channel();
            
            // Test queue operations
            $testQueue = 'test_queue_' . uniqid();
            
            // Declare queue
            $channel->queue_declare($testQueue, false, true, false, false);
            
            // Publish message
            $message = new AMQPMessage('test');
            $channel->basic_publish($message, '', $testQueue);
            
            // Consume message
            $received = false;
            $callback = function ($msg) use (&$received) {
                $received = true;
                $msg->delivery_info['channel']->basic_ack($msg->delivery_info['delivery_tag']);
            };
            
            $channel->basic_consume($testQueue, '', false, false, false, false, $callback);
            
            // Wait for message
            $channel->wait(null, false, $this->timeout);
            
            if (!$received) {
                throw new \RuntimeException("Failed to receive test message");
            }
            
            // Clean up
            $channel->queue_delete($testQueue);
            $channel->close();
        } catch (\Exception $e) {
            $this->addError("Initialization failed: " . $e->getMessage());
            throw $e;
        }
    }

    private function getConnection(): AMQPStreamConnection
    {
        if ($this->connection === null) {
            $this->connection = new AMQPStreamConnection(
                $this->config['host'],
                $this->config['port'],
                $this->config['user'],
                $this->config['password'],
                $this->config['vhost'],
                false,
                'AMQPLAIN',
                null,
                'en_US',
                $this->timeout,
                $this->timeout
            );
        }

        return $this->connection;
    }

    public function getConnectionInstance(): AMQPStreamConnection
    {
        return $this->getConnection();
    }
} 