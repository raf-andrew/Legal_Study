<?php

namespace LegalStudy\ModularInitialization\Services;

use RuntimeException;

class InitializationPerformanceMonitor
{
    private array $measurements = [];
    private array $currentMeasurements = [];

    public function startMeasurement(string $component, string $operation): void
    {
        $key = $this->getMeasurementKey($component, $operation);
        $this->currentMeasurements[$key] = microtime(true);
    }

    public function endMeasurement(string $component, string $operation): void
    {
        $key = $this->getMeasurementKey($component, $operation);
        if (!isset($this->currentMeasurements[$key])) {
            throw new RuntimeException("No measurement started for {$component}:{$operation}");
        }

        $duration = microtime(true) - $this->currentMeasurements[$key];
        unset($this->currentMeasurements[$key]);

        if (!isset($this->measurements[$key])) {
            $this->measurements[$key] = [
                'component' => $component,
                'operation' => $operation,
                'count' => 0,
                'total_duration' => 0,
                'min_duration' => $duration,
                'max_duration' => $duration,
                'durations' => []
            ];
        }

        $this->measurements[$key]['count']++;
        $this->measurements[$key]['total_duration'] += $duration;
        $this->measurements[$key]['min_duration'] = min($this->measurements[$key]['min_duration'], $duration);
        $this->measurements[$key]['max_duration'] = max($this->measurements[$key]['max_duration'], $duration);
        $this->measurements[$key]['durations'][] = $duration;
    }

    public function getMetrics(): array
    {
        return $this->measurements;
    }

    public function getComponentMetrics(string $component): array
    {
        $metrics = [];
        foreach ($this->measurements as $key => $measurement) {
            if ($measurement['component'] === $component) {
                $metrics[$measurement['operation']] = $measurement;
            }
        }
        return $metrics;
    }

    public function clearMetrics(): void
    {
        $this->measurements = [];
        $this->currentMeasurements = [];
    }

    public function getAverageDuration(string $component, string $operation): float
    {
        $key = $this->getMeasurementKey($component, $operation);
        if (!isset($this->measurements[$key])) {
            return 0.0;
        }
        return $this->measurements[$key]['total_duration'] / $this->measurements[$key]['count'];
    }

    public function getMinDuration(string $component, string $operation): float
    {
        $key = $this->getMeasurementKey($component, $operation);
        return $this->measurements[$key]['min_duration'] ?? 0.0;
    }

    public function getMaxDuration(string $component, string $operation): float
    {
        $key = $this->getMeasurementKey($component, $operation);
        return $this->measurements[$key]['max_duration'] ?? 0.0;
    }

    public function getTotalDuration(string $component, string $operation): float
    {
        $key = $this->getMeasurementKey($component, $operation);
        return $this->measurements[$key]['total_duration'] ?? 0.0;
    }

    public function getMeasurementCount(string $component, string $operation): int
    {
        $key = $this->getMeasurementKey($component, $operation);
        return $this->measurements[$key]['count'] ?? 0;
    }

    private function getMeasurementKey(string $component, string $operation): string
    {
        return "{$component}:{$operation}";
    }
} 