<?php

namespace Mcp\Events;

use Mcp\Agent\Agent;
use Mcp\Agent\Communication\AgentMessage;

class AgentMessageReceived extends AgentLifecycleEvent
{
    public AgentMessage $message;

    public function __construct(Agent $receiver, AgentMessage $message)
    {
        parent::__construct($receiver, 'message_received', [
            'sender_id' => $message->getSenderId(),
            'message_type' => $message->getType(),
            'message_data' => $message->getData()
        ]);
        
        $this->message = $message;
    }
} 