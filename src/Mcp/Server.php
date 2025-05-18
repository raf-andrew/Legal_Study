<?php

namespace LegalStudy\MCP;

use LegalStudy\Initialization\AbstractInitialization;
use LegalStudy\Initialization\InitializationStatus;
use LegalStudy\Initialization\InitializationPerformanceMonitor;
use Psr\Log\LoggerInterface;
use Psr\Log\NullLogger;

class Server extends AbstractInitialization
{
    private bool $enabled;
    private LoggerInterface $logger;
    private array $agents = [];
    private array $config = [];
    private bool $isProduction;

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

    public function registerAgent(string $name, AgentInterface $agent): void
    {
        if (!$this->enabled) {
            throw new \RuntimeException('Cannot register agent while MCP is disabled');
        }
        $this->agents[$name] = $agent;
        $this->logger->info("Agent registered: {$name}");
    }

    public function getAgent(string $name): ?AgentInterface
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
                $this->logger->info("Agent initialized: {$name}");
            } catch (\Exception $e) {
                $this->addError("Failed to initialize agent {$name}: " . $e->getMessage());
                $this->logger->error("Agent initialization failed: {$name}", ['exception' => $e]);
            }
        }
    }
} 