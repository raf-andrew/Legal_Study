<?php

namespace Mcp\Events;

use Mcp\Agent\Agent;

class AgentStateChanged extends AgentLifecycleEvent
{
    public function __construct(Agent $agent, string $newState)
    {
        parent::__construct($agent, 'state_changed', ['new_state' => $newState]);
    }
} 