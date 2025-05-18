<?php

namespace App\Mcp\Console\Commands;

use App\Mcp\Agent\Registry;
use App\Mcp\Server;
use Symfony\Component\Console\Input\InputArgument;
use Symfony\Component\Console\Input\InputOption;

class AgentCommand extends McpCommand
{
    protected $signature = 'mcp:agent 
                          {action : Action to perform (list|info|register|unregister|execute)} 
                          {agent? : Agent ID for specific operations}
                          {--capability= : Filter agents by capability}
                          {--action= : Action to execute}
                          {--params= : JSON-encoded parameters for execution}
                          {--format=table : Output format (table|json)}
                          {--force : Force the operation without confirmation}';

    protected $description = 'Manage MCP agents';

    protected $registry;

    public function __construct(Server $server)
    {
        parent::__construct($server);
        $this->registry = $server->getService(Registry::class);
    }

    public function handle()
    {
        $action = $this->argument('action');
        
        try {
            switch ($action) {
                case 'list':
                    return $this->listAgents();
                case 'info':
                    return $this->showAgentInfo();
                case 'register':
                    return $this->registerAgent();
                case 'unregister':
                    return $this->unregisterAgent();
                case 'execute':
                    return $this->executeAgentAction();
                default:
                    $this->error("Unknown action: {$action}");
                    return 1;
            }
        } catch (\Exception $e) {
            return $this->handleException($e);
        }
    }

    protected function listAgents()
    {
        $agents = $this->registry->getAgents();
        
        if ($capability = $this->option('capability')) {
            $agents = $this->registry->getAgentsWithCapability($capability);
        }

        $data = $agents->map(function ($agent) {
            return [
                'id' => $agent->getId(),
                'capabilities' => implode(', ', $agent->getCapabilities()),
                'state' => json_encode($agent->getState()),
            ];
        })->toArray();

        $this->line($this->formatOutput($data, $this->option('format')));
        return 0;
    }

    protected function showAgentInfo()
    {
        $agentId = $this->argument('agent');
        if (!$agentId) {
            $this->error('Agent ID is required');
            return 1;
        }

        $agent = $this->registry->getAgent($agentId);
        if (!$agent) {
            $this->error("Agent not found: {$agentId}");
            return 1;
        }

        $data = [
            'id' => $agent->getId(),
            'capabilities' => implode(', ', $agent->getCapabilities()),
            'state' => json_encode($agent->getState()),
            'metadata' => json_encode($agent->getMetadata()),
        ];

        $this->line($this->formatOutput($data, $this->option('format')));
        return 0;
    }

    protected function registerAgent()
    {
        $agentId = $this->argument('agent');
        if (!$agentId) {
            $this->error('Agent ID is required');
            return 1;
        }

        // In a real implementation, we would load the agent class dynamically
        // For now, we'll just show a placeholder message
        $this->info("Agent registration would happen here for: {$agentId}");
        return 0;
    }

    protected function unregisterAgent()
    {
        $agentId = $this->argument('agent');
        if (!$agentId) {
            $this->error('Agent ID is required');
            return 1;
        }

        $this->confirmAction("Are you sure you want to unregister agent: {$agentId}?");

        if ($this->registry->unregister($agentId)) {
            $this->info("Agent unregistered: {$agentId}");
            return 0;
        }

        $this->error("Failed to unregister agent: {$agentId}");
        return 1;
    }

    protected function executeAgentAction()
    {
        $agentId = $this->argument('agent');
        $action = $this->option('action');
        $params = json_decode($this->option('params') ?? '{}', true);

        if (!$agentId || !$action) {
            $this->error('Agent ID and action are required');
            return 1;
        }

        $agent = $this->registry->getAgent($agentId);
        if (!$agent) {
            $this->error("Agent not found: {$agentId}");
            return 1;
        }

        try {
            $result = $agent->execute($action, $params);
            $this->line($this->formatOutput($result, $this->option('format')));
            return 0;
        } catch (\Exception $e) {
            $this->error("Failed to execute action: {$e->getMessage()}");
            return 1;
        }
    }
} 