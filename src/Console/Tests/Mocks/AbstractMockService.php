<?php

namespace LegalStudy\Console\Tests\Mocks;

abstract class AbstractMockService implements MockServiceInterface
{
    protected string $name;
    protected array $config = [];
    protected bool $enabled = true;
    protected bool $shouldFail = false;
    protected array $status = [];

    public function __construct(string $name, array $config = [])
    {
        $this->name = $name;
        $this->config = $config;
        $this->reset();
    }

    public function getName(): string
    {
        return $this->name;
    }

    public function isAvailable(): bool
    {
        return $this->enabled && !$this->shouldFail;
    }

    public function getStatus(): array
    {
        return $this->status;
    }

    public function getConfig(): array
    {
        return $this->config;
    }

    public function setConfig(array $config): void
    {
        $this->config = array_merge($this->config, $config);
    }

    public function reset(): void
    {
        $this->enabled = true;
        $this->shouldFail = false;
        $this->status = [
            'enabled' => $this->enabled,
            'should_fail' => $this->shouldFail,
            'last_reset' => date('Y-m-d H:i:s')
        ];
    }

    public function enable(): void
    {
        $this->enabled = true;
        $this->updateStatus();
    }

    public function disable(): void
    {
        $this->enabled = false;
        $this->updateStatus();
    }

    public function setShouldFail(bool $shouldFail): void
    {
        $this->shouldFail = $shouldFail;
        $this->updateStatus();
    }

    public function shouldFail(): bool
    {
        return $this->shouldFail;
    }

    protected function updateStatus(): void
    {
        $this->status = [
            'enabled' => $this->enabled,
            'should_fail' => $this->shouldFail,
            'last_update' => date('Y-m-d H:i:s')
        ];
    }

    protected function throwIfShouldFail(): void
    {
        if ($this->shouldFail) {
            throw new \RuntimeException("Service '{$this->name}' is configured to fail");
        }
    }

    protected function throwIfDisabled(): void
    {
        if (!$this->enabled) {
            throw new \RuntimeException("Service '{$this->name}' is disabled");
        }
    }
} 