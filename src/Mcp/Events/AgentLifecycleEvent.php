<?php

namespace Mcp\Events;

use Mcp\Agent\Agent;

class AgentLifecycleEvent
{
    public Agent $agent;
    public string $event;
    public array $data;

    public function __construct(Agent $agent, string $event, array $data = [])
    {
        $this->agent = $agent;
        $this->event = $event;
        $this->data = $data;
    }
} 