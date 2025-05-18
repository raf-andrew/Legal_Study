<?php

namespace LegalStudy\ModularInitialization\Services;

use InvalidArgumentException;

class InitializationDataCollector
{
    private array $metrics = [];
    private array $timerData = [];
    private array $data = [];

    public function collectMetric(string $component, string $metric, mixed $value): void
    {
        if (!isset($this->metrics[$component])) {
            $this->metrics[$component] = [];
        }
        $this->metrics[$component][$metric] = $value;
    }

    public function getMetrics(?string $component = null): array
    {
        if ($component === null) {
            return $this->metrics;
        }
        return $this->metrics[$component] ?? [];
    }

    public function startTimer(string $component, string $operation): void
    {
        $key = $this->getTimerKey($component, $operation);
        $this->timerData[$key] = [
            'start' => microtime(true),
            'component' => $component,
            'operation' => $operation
        ];
    }

    public function endTimer(string $component, string $operation): float
    {
        $key = $this->getTimerKey($component, $operation);
        if (!isset($this->timerData[$key])) {
            throw new InvalidArgumentException("No timer started for {$component}:{$operation}");
        }

        $duration = microtime(true) - $this->timerData[$key]['start'];
        $this->timerData[$key]['duration'] = $duration;
        $this->timerData[$key]['end'] = microtime(true);

        return $duration;
    }

    public function getTimerData(?string $component = null): array
    {
        if ($component === null) {
            return $this->timerData;
        }

        $result = [];
        foreach ($this->timerData as $key => $data) {
            if ($data['component'] === $component) {
                $result[$key] = $data;
            }
        }
        return $result;
    }

    public function clearData(): void
    {
        $this->metrics = [];
        $this->timerData = [];
        $this->data = [];
    }

    public function addData(string $key, mixed $value): void
    {
        $this->data[$key] = $value;
    }

    public function getData(string $key): mixed
    {
        return $this->data[$key] ?? null;
    }

    public function getAllData(): array
    {
        return [
            'metrics' => $this->metrics,
            'timers' => $this->timerData,
            'data' => $this->data
        ];
    }

    private function getTimerKey(string $component, string $operation): string
    {
        return "{$component}:{$operation}";
    }
} 