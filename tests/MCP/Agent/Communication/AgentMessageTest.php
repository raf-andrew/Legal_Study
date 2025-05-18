<?php

namespace Tests\Mcp\Agent\Communication;

use Mcp\Agent\Communication\AgentMessage;
use Tests\TestCase;

class AgentMessageTest extends TestCase
{
    private AgentMessage $message;
    private string $type = 'test.message';
    private string $senderId = 'sender-123';
    private string $receiverId = 'receiver-456';
    private array $payload = ['key' => 'value'];

    protected function setUp(): void
    {
        parent::setUp();
        
        $this->message = new AgentMessage(
            $this->type,
            $this->senderId,
            $this->payload,
            $this->receiverId,
            true,
            null,
            3600
        );
    }

    public function testMessageConstruction(): void
    {
        $this->assertNotEmpty($this->message->getId());
        $this->assertEquals($this->type, $this->message->getType());
        $this->assertEquals($this->senderId, $this->message->getSenderId());
        $this->assertEquals($this->receiverId, $this->message->getReceiverId());
        $this->assertEquals($this->payload, $this->message->getPayload());
        $this->assertTrue($this->message->requiresResponse());
        $this->assertNull($this->message->getCorrelationId());
        $this->assertEquals(3600, $this->message->getTtl());
        $this->assertIsInt($this->message->getTimestamp());
    }

    public function testMessageWithoutReceiver(): void
    {
        $message = new AgentMessage(
            $this->type,
            $this->senderId,
            $this->payload
        );
        
        $this->assertNull($message->getReceiverId());
    }

    public function testMessageExpiration(): void
    {
        $message = new AgentMessage(
            $this->type,
            $this->senderId,
            $this->payload,
            null,
            false,
            null,
            -1 // Expired immediately
        );
        
        $this->assertTrue($message->isExpired());
        
        $message = new AgentMessage(
            $this->type,
            $this->senderId,
            $this->payload,
            null,
            false,
            null,
            3600
        );
        
        $this->assertFalse($message->isExpired());
    }

    public function testResponseCreation(): void
    {
        $responsePayload = ['status' => 'success'];
        $response = $this->message->createResponse($responsePayload);
        
        $this->assertEquals($this->type . '.response', $response->getType());
        $this->assertEquals($this->receiverId, $response->getSenderId());
        $this->assertEquals($this->senderId, $response->getReceiverId());
        $this->assertEquals($responsePayload, $response->getPayload());
        $this->assertFalse($response->requiresResponse());
        $this->assertEquals($this->message->getId(), $response->getCorrelationId());
    }

    public function testJsonSerialization(): void
    {
        $json = json_encode($this->message);
        $data = json_decode($json, true);
        
        $this->assertArrayHasKey('id', $data);
        $this->assertArrayHasKey('type', $data);
        $this->assertArrayHasKey('sender_id', $data);
        $this->assertArrayHasKey('receiver_id', $data);
        $this->assertArrayHasKey('payload', $data);
        $this->assertArrayHasKey('timestamp', $data);
        $this->assertArrayHasKey('ttl', $data);
        $this->assertArrayHasKey('requires_response', $data);
        $this->assertArrayHasKey('correlation_id', $data);
        
        $this->assertEquals($this->type, $data['type']);
        $this->assertEquals($this->senderId, $data['sender_id']);
        $this->assertEquals($this->receiverId, $data['receiver_id']);
        $this->assertEquals($this->payload, $data['payload']);
    }

    public function testFromArray(): void
    {
        $data = [
            'id' => 'test-id',
            'type' => $this->type,
            'sender_id' => $this->senderId,
            'receiver_id' => $this->receiverId,
            'payload' => $this->payload,
            'timestamp' => time(),
            'ttl' => 3600,
            'requires_response' => true,
            'correlation_id' => 'correlation-id'
        ];
        
        $message = AgentMessage::fromArray($data);
        
        $this->assertEquals($data['id'], $message->getId());
        $this->assertEquals($data['type'], $message->getType());
        $this->assertEquals($data['sender_id'], $message->getSenderId());
        $this->assertEquals($data['receiver_id'], $message->getReceiverId());
        $this->assertEquals($data['payload'], $message->getPayload());
        $this->assertEquals($data['timestamp'], $message->getTimestamp());
        $this->assertEquals($data['ttl'], $message->getTtl());
        $this->assertTrue($message->requiresResponse());
        $this->assertEquals($data['correlation_id'], $message->getCorrelationId());
    }

    public function testFromArrayWithDefaults(): void
    {
        $data = [
            'id' => 'test-id',
            'type' => $this->type,
            'sender_id' => $this->senderId,
            'payload' => $this->payload,
            'timestamp' => time()
        ];
        
        $message = AgentMessage::fromArray($data);
        
        $this->assertNull($message->getReceiverId());
        $this->assertFalse($message->requiresResponse());
        $this->assertNull($message->getCorrelationId());
        $this->assertEquals(3600, $message->getTtl());
    }
} 