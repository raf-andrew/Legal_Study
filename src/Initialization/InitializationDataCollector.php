<?php

namespace LegalStudy\Initialization;

class InitializationDataCollector
{
    private array $data = [];
    private array $metrics = [];
    private array $timestamps = [];

    public function collectData(string $component, string $key, mixed $value): void
    {
        if (!isset($this->data[$component])) {
            $this->data[$component] = [];
        }
        $this->data[$component][$key] = $value;
    }

    public function collectMetric(string $component, string $metric, float $value): void
    {
        if (!isset($this->metrics[$component])) {
            $this->metrics[$component] = [];
        }
        $this->metrics[$component][$metric] = $value;
    }

    public function startTimer(string $component, string $operation): void
    {
        $key = $this->getTimerKey($component, $operation);
        $this->timestamps[$key] = [
            'start' => microtime(true),
            'end' => null
        ];
    }

    public function stopTimer(string $component, string $operation): float
    {
        $key = $this->getTimerKey($component, $operation);
        if (!isset($this->timestamps[$key])) {
            throw new \RuntimeException("Timer not started for component '{$component}' operation '{$operation}'");
        }

        $this->timestamps[$key]['end'] = microtime(true);
        return $this->timestamps[$key]['end'] - $this->timestamps[$key]['start'];
    }

    public function getData(string $component, ?string $key = null): mixed
    {
        if (!isset($this->data[$component])) {
            return null;
        }

        if ($key === null) {
            return $this->data[$component];
        }

        return $this->data[$component][$key] ?? null;
    }

    public function getMetrics(string $component, ?string $metric = null): mixed
    {
        if (!isset($this->metrics[$component])) {
            return null;
        }

        if ($metric === null) {
            return $this->metrics[$component];
        }

        return $this->metrics[$component][$metric] ?? null;
    }

    public function getTimerData(string $component, string $operation): ?array
    {
        $key = $this->getTimerKey($component, $operation);
        return $this->timestamps[$key] ?? null;
    }

    public function getAllData(): array
    {
        return [
            'data' => $this->data,
            'metrics' => $this->metrics,
            'timestamps' => $this->timestamps
        ];
    }

    public function clearData(): void
    {
        $this->data = [];
        $this->metrics = [];
        $this->timestamps = [];
    }

    private function getTimerKey(string $component, string $operation): string
    {
        return "{$component}:{$operation}";
    }
} 