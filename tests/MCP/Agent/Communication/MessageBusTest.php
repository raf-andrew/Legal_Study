<?php

namespace Tests\Mcp\Agent\Communication;

use Mcp\Agent\Communication\MessageBus;
use Mcp\Agent\Communication\AgentMessage;
use Tests\TestCase;
use Illuminate\Support\Facades\Cache;
use Illuminate\Support\Facades\Log;
use Illuminate\Support\Facades\Event;
use Mockery;

class MessageBusTest extends TestCase
{
    private MessageBus $bus;
    private AgentMessage $message;
    private string $senderId = 'sender-123';
    private string $receiverId = 'receiver-456';

    protected function setUp(): void
    {
        parent::setUp();
        
        Cache::flush();
        
        $this->bus = new MessageBus();
        $this->message = new AgentMessage(
            'test.message',
            $this->senderId,
            ['key' => 'value'],
            $this->receiverId
        );
    }

    public function testMessagePublishing(): void
    {
        Event::fake();
        Log::shouldReceive('info')
            ->once()
            ->with("Message published: {$this->message->getId()} of type {$this->message->getType()}");

        $this->bus->publish($this->message);
        
        Event::assertDispatched('mcp.message.published', function ($eventName, $args) {
            return $args[0] === $this->message;
        });
        
        $messages = $this->bus->getMessages($this->receiverId);
        $this->assertEquals(1, $messages->count());
        $this->assertEquals($this->message, $messages->first());
    }

    public function testExpiredMessagePublishing(): void
    {
        $expiredMessage = new AgentMessage(
            'test.message',
            $this->senderId,
            ['key' => 'value'],
            $this->receiverId,
            false,
            null,
            -1
        );

        Log::shouldReceive('warning')
            ->once()
            ->with("Attempted to publish expired message: {$expiredMessage->getId()}");

        $this->bus->publish($expiredMessage);
        
        $messages = $this->bus->getMessages($this->receiverId);
        $this->assertEquals(0, $messages->count());
    }

    public function testMessageSubscription(): void
    {
        Event::fake();
        
        $messageTypes = ['test.message', 'test.notification'];
        
        Log::shouldReceive('info')
            ->once()
            ->with("Agent {$this->senderId} subscribed to message types: " . implode(', ', $messageTypes));

        $this->bus->subscribe($this->senderId, $messageTypes);
        
        $broadcastMessage = new AgentMessage(
            'test.message',
            'other-sender',
            ['key' => 'value']
        );

        Log::shouldReceive('info')
            ->once()
            ->with("Message published: {$broadcastMessage->getId()} of type {$broadcastMessage->getType()}");
        
        Log::shouldReceive('info')
            ->once()
            ->with("Notified agent {$this->senderId} about message {$broadcastMessage->getId()}");

        $this->bus->publish($broadcastMessage);
        
        Event::assertDispatched('mcp.message.received', function ($eventName, $args) use ($broadcastMessage) {
            return $args[0] === $broadcastMessage && $args[1] === $this->senderId;
        });
    }

    public function testMessageUnsubscription(): void
    {
        $messageTypes = ['test.message', 'test.notification'];
        $this->bus->subscribe($this->senderId, $messageTypes);

        Log::shouldReceive('info')
            ->once()
            ->with("Agent {$this->senderId} unsubscribed from message types");

        $this->bus->unsubscribe($this->senderId, ['test.message']);
        
        $broadcastMessage = new AgentMessage(
            'test.message',
            'other-sender',
            ['key' => 'value']
        );

        Log::shouldReceive('info')
            ->once()
            ->with("Message published: {$broadcastMessage->getId()} of type {$broadcastMessage->getType()}");

        $this->bus->publish($broadcastMessage);
        
        $messages = $this->bus->getMessages($this->senderId);
        $this->assertEquals(0, $messages->count());
    }

    public function testMessageAcknowledgement(): void
    {
        $this->bus->publish($this->message);

        Log::shouldReceive('info')
            ->once()
            ->with("Message {$this->message->getId()} acknowledged by agent {$this->receiverId}");

        $this->bus->acknowledgeMessage($this->message->getId(), $this->receiverId);
        
        $messages = $this->bus->getMessages($this->receiverId);
        $this->assertEquals(0, $messages->count());
    }

    public function testInvalidMessageAcknowledgement(): void
    {
        Log::shouldReceive('warning')
            ->once()
            ->with("Attempted to acknowledge non-existent message: invalid-id");

        $this->bus->acknowledgeMessage('invalid-id', $this->receiverId);
    }

    public function testUnauthorizedMessageAcknowledgement(): void
    {
        $this->bus->publish($this->message);

        Log::shouldReceive('warning')
            ->once()
            ->with("Agent unauthorized-agent attempted to acknowledge message {$this->message->getId()} intended for {$this->receiverId}");

        $this->bus->acknowledgeMessage($this->message->getId(), 'unauthorized-agent');
        
        $messages = $this->bus->getMessages($this->receiverId);
        $this->assertEquals(1, $messages->count());
    }

    public function testClearExpiredMessages(): void
    {
        $expiredMessage = new AgentMessage(
            'test.message',
            $this->senderId,
            ['key' => 'value'],
            $this->receiverId,
            false,
            null,
            -1
        );

        Log::shouldReceive('info')
            ->once()
            ->with("Message published: {$expiredMessage->getId()} of type {$expiredMessage->getType()}");

        $this->bus->publish($expiredMessage);
        $this->bus->publish($this->message);

        Log::shouldReceive('info')
            ->once()
            ->with("Cleared 1 expired messages");

        $this->bus->clearExpiredMessages();
        
        $messages = $this->bus->getMessages($this->receiverId);
        $this->assertEquals(1, $messages->count());
        $this->assertEquals($this->message, $messages->first());
    }

    public function testMessagePersistence(): void
    {
        $this->bus->publish($this->message);
        
        $newBus = new MessageBus();
        $messages = $newBus->getMessages($this->receiverId);
        
        $this->assertEquals(1, $messages->count());
        $this->assertEquals($this->message->getId(), $messages->first()->getId());
    }

    public function testSubscriptionPersistence(): void
    {
        $messageTypes = ['test.message', 'test.notification'];
        $this->bus->subscribe($this->senderId, $messageTypes);
        
        $newBus = new MessageBus();
        $broadcastMessage = new AgentMessage(
            'test.message',
            'other-sender',
            ['key' => 'value']
        );
        
        $newBus->publish($broadcastMessage);
        
        $messages = $newBus->getMessages($this->senderId);
        $this->assertEquals(1, $messages->count());
    }
} 