<?php

namespace Tests\Mcp\Agent\Communication;

use Tests\TestCase;
use Mcp\Agent\Agent;
use Mcp\Agent\Communication\AgentCommunicationManager;
use Mcp\Agent\Communication\AgentMessage;
use Illuminate\Support\Facades\Cache;
use Illuminate\Support\Facades\Event;
use Mcp\Events\AgentMessageSent;
use Mcp\Events\AgentMessageReceived;
use Mcp\Events\AgentCommunicationError;

class AgentCommunicationManagerTest extends TestCase
{
    protected AgentCommunicationManager $communicationManager;
    protected Agent $senderAgent;
    protected Agent $receiverAgent;

    protected function setUp(): void
    {
        parent::setUp();
        
        $this->communicationManager = new AgentCommunicationManager();
        $this->senderAgent = new Agent('Sender Agent', 'test', ['test_capability']);
        $this->receiverAgent = new Agent('Receiver Agent', 'test', ['test_capability']);
        
        Cache::forget('mcp.agent.communication.queues');
        Cache::forget('mcp.agent.communication.history');
        Event::fake();
    }

    public function test_send_message(): void
    {
        $messageType = 'test_message';
        $messageData = ['test' => 'data'];
        
        $this->communicationManager->sendMessage($this->senderAgent, $this->receiverAgent, $messageType, $messageData);
        
        $queue = $this->communicationManager->getMessageQueue($this->receiverAgent);
        $this->assertCount(1, $queue);
        
        $message = $queue->first();
        $this->assertEquals($this->senderAgent->getId(), $message->getSenderId());
        $this->assertEquals($this->receiverAgent->getId(), $message->getReceiverId());
        $this->assertEquals($messageType, $message->getType());
        $this->assertEquals($messageData, $message->getData());
        
        Event::assertDispatched(AgentMessageSent::class, function ($event) {
            return $event->agent->getId() === $this->senderAgent->getId() &&
                   $event->receiver->getId() === $this->receiverAgent->getId();
        });
    }

    public function test_receive_message(): void
    {
        $messageType = 'test_message';
        $messageData = ['test' => 'data'];
        
        $this->communicationManager->sendMessage($this->senderAgent, $this->receiverAgent, $messageType, $messageData);
        
        $message = $this->communicationManager->receiveMessage($this->receiverAgent);
        $this->assertNotNull($message);
        $this->assertEquals($this->senderAgent->getId(), $message->getSenderId());
        $this->assertEquals($this->receiverAgent->getId(), $message->getReceiverId());
        $this->assertEquals($messageType, $message->getType());
        $this->assertEquals($messageData, $message->getData());
        
        Event::assertDispatched(AgentMessageReceived::class, function ($event) {
            return $event->agent->getId() === $this->receiverAgent->getId();
        });
    }

    public function test_receive_message_empty_queue(): void
    {
        $message = $this->communicationManager->receiveMessage($this->receiverAgent);
        $this->assertNull($message);
    }

    public function test_get_message_history(): void
    {
        $messageType = 'test_message';
        $messageData = ['test' => 'data'];
        
        $this->communicationManager->sendMessage($this->senderAgent, $this->receiverAgent, $messageType, $messageData);
        
        $history = $this->communicationManager->getMessageHistory($this->receiverAgent);
        $this->assertCount(1, $history);
        
        $message = $history->first();
        $this->assertEquals($this->senderAgent->getId(), $message->getSenderId());
        $this->assertEquals($this->receiverAgent->getId(), $message->getReceiverId());
        $this->assertEquals($messageType, $message->getType());
        $this->assertEquals($messageData, $message->getData());
    }

    public function test_clear_message_queue(): void
    {
        $messageType = 'test_message';
        $messageData = ['test' => 'data'];
        
        $this->communicationManager->sendMessage($this->senderAgent, $this->receiverAgent, $messageType, $messageData);
        
        $queue = $this->communicationManager->getMessageQueue($this->receiverAgent);
        $this->assertCount(1, $queue);
        
        $this->communicationManager->clearMessageQueue($this->receiverAgent);
        
        $queue = $this->communicationManager->getMessageQueue($this->receiverAgent);
        $this->assertCount(0, $queue);
    }

    public function test_record_communication_error(): void
    {
        $error = new \RuntimeException('Test error');
        
        $this->communicationManager->recordCommunicationError($this->senderAgent, $error);
        
        Event::assertDispatched(AgentCommunicationError::class, function ($event) use ($error) {
            return $event->agent->getId() === $this->senderAgent->getId() &&
                   $event->data['message'] === $error->getMessage();
        });
    }
} 