<?php

namespace LegalStudy\MCP\Agent;

use Psr\Log\LoggerInterface;
use Psr\Log\NullLogger;
use DateTimeImmutable;

abstract class AbstractAgent implements AgentLifecycleInterface
{
    protected LoggerInterface $logger;
    protected string $state = self::STATE_STOPPED;
    protected ?string $lastError = null;
    protected ?DateTimeImmutable $startTime = null;
    protected array $statistics = [];

    public function __construct(?LoggerInterface $logger = null)
    {
        $this->logger = $logger ?? new NullLogger();
    }

    public function initialize(): void
    {
        try {
            $this->doInitialize();
            $this->state = self::STATE_INITIALIZED;
            $this->logger->info('Agent initialized successfully');
        } catch (\Exception $e) {
            $this->state = self::STATE_ERROR;
            $this->lastError = $e->getMessage();
            $this->logger->error('Agent initialization failed', ['error' => $e->getMessage()]);
            throw $e;
        }
    }

    public function start(): void
    {
        if ($this->state !== self::STATE_INITIALIZED && $this->state !== self::STATE_STOPPED) {
            throw new \RuntimeException('Agent must be initialized or stopped to start');
        }

        try {
            $this->doStart();
            $this->state = self::STATE_STARTED;
            $this->startTime = new DateTimeImmutable();
            $this->logger->info('Agent started successfully');
        } catch (\Exception $e) {
            $this->state = self::STATE_ERROR;
            $this->lastError = $e->getMessage();
            $this->logger->error('Agent start failed', ['error' => $e->getMessage()]);
            throw $e;
        }
    }

    public function stop(): void
    {
        if ($this->state !== self::STATE_STARTED && $this->state !== self::STATE_PAUSED) {
            throw new \RuntimeException('Agent must be started or paused to stop');
        }

        try {
            $this->doStop();
            $this->state = self::STATE_STOPPED;
            $this->startTime = null;
            $this->logger->info('Agent stopped successfully');
        } catch (\Exception $e) {
            $this->state = self::STATE_ERROR;
            $this->lastError = $e->getMessage();
            $this->logger->error('Agent stop failed', ['error' => $e->getMessage()]);
            throw $e;
        }
    }

    public function pause(): void
    {
        if ($this->state !== self::STATE_STARTED) {
            throw new \RuntimeException('Agent must be started to pause');
        }

        try {
            $this->doPause();
            $this->state = self::STATE_PAUSED;
            $this->logger->info('Agent paused successfully');
        } catch (\Exception $e) {
            $this->state = self::STATE_ERROR;
            $this->lastError = $e->getMessage();
            $this->logger->error('Agent pause failed', ['error' => $e->getMessage()]);
            throw $e;
        }
    }

    public function resume(): void
    {
        if ($this->state !== self::STATE_PAUSED) {
            throw new \RuntimeException('Agent must be paused to resume');
        }

        try {
            $this->doResume();
            $this->state = self::STATE_STARTED;
            $this->logger->info('Agent resumed successfully');
        } catch (\Exception $e) {
            $this->state = self::STATE_ERROR;
            $this->lastError = $e->getMessage();
            $this->logger->error('Agent resume failed', ['error' => $e->getMessage()]);
            throw $e;
        }
    }

    public function restart(): void
    {
        if ($this->state === self::STATE_STARTED || $this->state === self::STATE_PAUSED) {
            $this->stop();
        }
        $this->start();
    }

    public function getState(): string
    {
        return $this->state;
    }

    public function isHealthy(): bool
    {
        return $this->state !== self::STATE_ERROR;
    }

    public function getLastError(): ?string
    {
        return $this->lastError;
    }

    public function getUptime(): int
    {
        if ($this->startTime === null) {
            return 0;
        }

        return (new DateTimeImmutable())->getTimestamp() - $this->startTime->getTimestamp();
    }

    public function getStatistics(): array
    {
        return array_merge([
            'state' => $this->state,
            'uptime' => $this->getUptime(),
            'last_error' => $this->lastError,
            'is_healthy' => $this->isHealthy(),
        ], $this->statistics);
    }

    /**
     * Initialize the agent's specific functionality
     * @throws \RuntimeException if initialization fails
     */
    abstract protected function doInitialize(): void;

    /**
     * Start the agent's specific functionality
     * @throws \RuntimeException if start fails
     */
    abstract protected function doStart(): void;

    /**
     * Stop the agent's specific functionality
     * @throws \RuntimeException if stop fails
     */
    abstract protected function doStop(): void;

    /**
     * Pause the agent's specific functionality
     * @throws \RuntimeException if pause fails
     */
    abstract protected function doPause(): void;

    /**
     * Resume the agent's specific functionality
     * @throws \RuntimeException if resume fails
     */
    abstract protected function doResume(): void;
} 