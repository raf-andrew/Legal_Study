<?php

namespace App\Mcp\Agent;

class TestAgent extends BaseAgent
{
    protected function initialize()
    {
        $this->addCapability('test');
        $this->addCapability('debug');
        $this->updateMetadata([
            'version' => '1.0.0',
            'description' => 'Test agent for MCP system',
        ]);
    }

    public function execute(string $action, array $parameters = [])
    {
        switch ($action) {
            case 'echo':
                return $this->handleEcho($parameters);
            case 'sum':
                return $this->handleSum($parameters);
            case 'status':
                return $this->getState();
            default:
                $this->log("Unknown action: {$action}", 'warning');
                return null;
        }
    }

    protected function handleEcho(array $parameters)
    {
        $message = $parameters['message'] ?? '';
        $this->log("Echo: {$message}");
        return $message;
    }

    protected function handleSum(array $parameters)
    {
        $numbers = $parameters['numbers'] ?? [];
        if (!is_array($numbers)) {
            $this->log("Invalid numbers parameter", 'warning');
            return null;
        }

        $sum = array_sum($numbers);
        $this->log("Sum calculated: {$sum}");
        return $sum;
    }

    protected function handleTestEvent(array $data)
    {
        $this->log("Test event received: " . json_encode($data));
        $this->updateState(['last_event' => $data]);
    }
} 