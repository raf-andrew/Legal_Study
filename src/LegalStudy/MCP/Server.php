<?php

namespace LegalStudy\MCP;

use LegalStudy\Initialization\AbstractInitialization;
use LegalStudy\Initialization\InitializationStatus;
use LegalStudy\Initialization\InitializationPerformanceMonitor;
use LegalStudy\MCP\Agent\AgentLifecycleInterface;
use Psr\Log\LoggerInterface;
use Psr\Log\NullLogger;

class Server extends AbstractInitialization
{
    private bool $enabled;
    private LoggerInterface $logger;
    private array $agents = [];
    protected array $config = [];
    private bool $isProduction;
    private array $agentStates = [];
    private array $agentErrors = [];
    private array $agentStatistics = [];

    public function __construct(
        ?LoggerInterface $logger = null,
        bool $isProduction = false
    ) {
        parent::__construct();
        $this->logger = $logger ?? new NullLogger();
        $this->isProduction = $isProduction;
        $this->enabled = !$isProduction; // Disabled by default in production
    }

    public function isEnabled(): bool
    {
        return $this->enabled;
    }

    public function enable(): void
    {
        if ($this->isProduction) {
            throw new \RuntimeException('Cannot enable MCP in production environment');
        }
        $this->enabled = true;
        $this->logger->info('MCP Server enabled');
    }

    public function disable(): void
    {
        $this->enabled = false;
        $this->logger->info('MCP Server disabled');
    }

    public function registerAgent(string $name, AgentLifecycleInterface $agent): void
    {
        if (!$this->enabled) {
            throw new \RuntimeException('Cannot register agent while MCP is disabled');
        }
        $this->agents[$name] = $agent;
        $this->agentStates[$name] = $agent->getState();
        $this->agentErrors[$name] = $agent->getLastError();
        $this->agentStatistics[$name] = $agent->getStatistics();
        $this->logger->info("Agent registered: {$name}");
    }

    public function getAgent(string $name): ?AgentLifecycleInterface
    {
        return $this->agents[$name] ?? null;
    }

    public function getAgents(): array
    {
        return $this->agents;
    }

    public function setConfig(array $config): void
    {
        $this->config = $config;
        $this->logger->info('MCP configuration updated');
    }

    public function getConfig(): array
    {
        return $this->config;
    }

    public function startAgent(string $name): void
    {
        if (!$this->enabled) {
            throw new \RuntimeException('Cannot start agent while MCP is disabled');
        }

        $agent = $this->getAgent($name);
        if (!$agent) {
            throw new \RuntimeException("Agent not found: {$name}");
        }

        try {
            $agent->start();
            $this->updateAgentState($name);
            $this->logger->info("Agent started: {$name}");
        } catch (\Exception $e) {
            $this->logger->error("Failed to start agent {$name}", ['error' => $e->getMessage()]);
            throw $e;
        }
    }

    public function stopAgent(string $name): void
    {
        if (!$this->enabled) {
            throw new \RuntimeException('Cannot stop agent while MCP is disabled');
        }

        $agent = $this->getAgent($name);
        if (!$agent) {
            throw new \RuntimeException("Agent not found: {$name}");
        }

        try {
            $agent->stop();
            $this->updateAgentState($name);
            $this->logger->info("Agent stopped: {$name}");
        } catch (\Exception $e) {
            $this->logger->error("Failed to stop agent {$name}", ['error' => $e->getMessage()]);
            throw $e;
        }
    }

    public function pauseAgent(string $name): void
    {
        if (!$this->enabled) {
            throw new \RuntimeException('Cannot pause agent while MCP is disabled');
        }

        $agent = $this->getAgent($name);
        if (!$agent) {
            throw new \RuntimeException("Agent not found: {$name}");
        }

        try {
            $agent->pause();
            $this->updateAgentState($name);
            $this->logger->info("Agent paused: {$name}");
        } catch (\Exception $e) {
            $this->logger->error("Failed to pause agent {$name}", ['error' => $e->getMessage()]);
            throw $e;
        }
    }

    public function resumeAgent(string $name): void
    {
        if (!$this->enabled) {
            throw new \RuntimeException('Cannot resume agent while MCP is disabled');
        }

        $agent = $this->getAgent($name);
        if (!$agent) {
            throw new \RuntimeException("Agent not found: {$name}");
        }

        try {
            $agent->resume();
            $this->updateAgentState($name);
            $this->logger->info("Agent resumed: {$name}");
        } catch (\Exception $e) {
            $this->logger->error("Failed to resume agent {$name}", ['error' => $e->getMessage()]);
            throw $e;
        }
    }

    public function restartAgent(string $name): void
    {
        if (!$this->enabled) {
            throw new \RuntimeException('Cannot restart agent while MCP is disabled');
        }

        $agent = $this->getAgent($name);
        if (!$agent) {
            throw new \RuntimeException("Agent not found: {$name}");
        }

        try {
            $agent->restart();
            $this->updateAgentState($name);
            $this->logger->info("Agent restarted: {$name}");
        } catch (\Exception $e) {
            $this->logger->error("Failed to restart agent {$name}", ['error' => $e->getMessage()]);
            throw $e;
        }
    }

    public function getAgentState(string $name): string
    {
        return $this->agentStates[$name] ?? 'unknown';
    }

    public function getAgentError(string $name): ?string
    {
        return $this->agentErrors[$name] ?? null;
    }

    public function getAgentStatistics(string $name): array
    {
        return $this->agentStatistics[$name] ?? [];
    }

    public function getAllAgentStates(): array
    {
        return $this->agentStates;
    }

    public function getAllAgentErrors(): array
    {
        return $this->agentErrors;
    }

    public function getAllAgentStatistics(): array
    {
        return $this->agentStatistics;
    }

    protected function doValidateConfiguration(array $config): bool
    {
        // Basic configuration validation
        return isset($config['security']) && is_array($config['security']);
    }

    protected function doTestConnection(): bool
    {
        // Test basic connectivity
        return true;
    }

    protected function doPerformInitialization(): void
    {
        if (!$this->enabled) {
            throw new \RuntimeException('Cannot initialize MCP while disabled');
        }

        // Initialize all registered agents
        foreach ($this->agents as $name => $agent) {
            try {
                $agent->initialize();
                $this->updateAgentState($name);
                $this->logger->info("Agent initialized: {$name}");
            } catch (\Exception $e) {
                $this->addError("Failed to initialize agent {$name}: " . $e->getMessage());
                $this->logger->error("Agent initialization failed: {$name}", ['exception' => $e]);
            }
        }
    }

    private function updateAgentState(string $name): void
    {
        $agent = $this->getAgent($name);
        if ($agent) {
            $this->agentStates[$name] = $agent->getState();
            $this->agentErrors[$name] = $agent->getLastError();
            $this->agentStatistics[$name] = $agent->getStatistics();
        }
    }
} 