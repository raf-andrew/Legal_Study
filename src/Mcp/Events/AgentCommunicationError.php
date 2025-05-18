<?php

namespace Mcp\Events;

use Mcp\Agent\Agent;

class AgentCommunicationError extends AgentLifecycleEvent
{
    public function __construct(Agent $agent, \Throwable $error)
    {
        parent::__construct($agent, 'communication_error', [
            'message' => $error->getMessage(),
            'code' => $error->getCode(),
            'file' => $error->getFile(),
            'line' => $error->getLine(),
            'trace' => $error->getTraceAsString()
        ]);
    }
} 