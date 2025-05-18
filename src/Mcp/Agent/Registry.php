<?php

namespace App\Mcp\Agent;

use Illuminate\Support\Facades\Log;
use Illuminate\Support\Collection;

class Registry
{
    protected $agents = [];
    protected $capabilities = [];

    public function register(AgentInterface $agent)
    {
        $agentId = $agent->getId();
        
        if (isset($this->agents[$agentId])) {
            Log::warning("MCP Agent already registered: {$agentId}");
            return false;
        }

        $this->agents[$agentId] = $agent;
        $this->updateCapabilities($agent);

        Log::info("MCP Agent registered: {$agentId}");
        return true;
    }

    public function unregister($agentId)
    {
        if (!isset($this->agents[$agentId])) {
            return false;
        }

        unset($this->agents[$agentId]);
        $this->recalculateCapabilities();

        Log::info("MCP Agent unregistered: {$agentId}");
        return true;
    }

    public function getAgent($agentId)
    {
        return $this->agents[$agentId] ?? null;
    }

    public function getAgents()
    {
        return new Collection($this->agents);
    }

    public function getCapabilities()
    {
        return $this->capabilities;
    }

    public function getAgentsWithCapability($capability)
    {
        return $this->getAgents()->filter(function ($agent) use ($capability) {
            return $agent->hasCapability($capability);
        });
    }

    protected function updateCapabilities(AgentInterface $agent)
    {
        foreach ($agent->getCapabilities() as $capability) {
            if (!isset($this->capabilities[$capability])) {
                $this->capabilities[$capability] = [];
            }
            $this->capabilities[$capability][] = $agent->getId();
        }
    }

    protected function recalculateCapabilities()
    {
        $this->capabilities = [];
        foreach ($this->agents as $agent) {
            $this->updateCapabilities($agent);
        }
    }

    public function validateAgent(AgentInterface $agent)
    {
        $errors = [];

        // Validate agent ID
        if (empty($agent->getId())) {
            $errors[] = 'Agent ID is required';
        }

        // Validate capabilities
        $capabilities = $agent->getCapabilities();
        if (empty($capabilities)) {
            $errors[] = 'Agent must have at least one capability';
        }

        // Validate required methods
        $requiredMethods = ['getId', 'getCapabilities', 'hasCapability', 'execute'];
        foreach ($requiredMethods as $method) {
            if (!method_exists($agent, $method)) {
                $errors[] = "Agent must implement {$method} method";
            }
        }

        return $errors;
    }
} 