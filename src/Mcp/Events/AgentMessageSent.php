<?php

namespace Mcp\Events;

use Mcp\Agent\Agent;
use Mcp\Agent\Communication\AgentMessage;

class AgentMessageSent extends AgentLifecycleEvent
{
    public Agent $receiver;
    public AgentMessage $message;

    public function __construct(Agent $sender, Agent $receiver, AgentMessage $message)
    {
        parent::__construct($sender, 'message_sent', [
            'receiver_id' => $receiver->getId(),
            'message_type' => $message->getType(),
            'message_data' => $message->getData()
        ]);
        
        $this->receiver = $receiver;
        $this->message = $message;
    }
} 