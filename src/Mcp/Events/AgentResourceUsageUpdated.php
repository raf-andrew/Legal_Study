<?php

namespace Mcp\Events;

use Mcp\Agent\Agent;

class AgentResourceUsageUpdated extends AgentLifecycleEvent
{
    public function __construct(Agent $agent, float $memoryUsage, float $cpuUsage)
    {
        parent::__construct($agent, 'resource_usage_updated', [
            'memory_usage' => $memoryUsage,
            'cpu_usage' => $cpuUsage,
            'timestamp' => now()
        ]);
    }
} 