<?php

namespace LegalStudy\Initialization;

class InitializationPerformanceMonitor
{
    private array $metrics = [];
    private array $thresholds = [];

    public function startMeasurement(string $component, string $operation): void
    {
        if (!isset($this->metrics[$component])) {
            $this->metrics[$component] = [];
        }
        if (!isset($this->metrics[$component][$operation])) {
            $this->metrics[$component][$operation] = [
                'start_time' => microtime(true),
                'end_time' => null,
                'min_duration' => PHP_FLOAT_MAX,
                'max_duration' => 0,
                'total_duration' => 0,
                'count' => 0
            ];
        }
        $this->metrics[$component][$operation]['start_time'] = microtime(true);
    }

    public function endMeasurement(string $component, string $operation): void
    {
        if (!isset($this->metrics[$component][$operation])) {
            throw new \RuntimeException("Measurement not started for component '$component' and operation '$operation'");
        }
        
        $this->metrics[$component][$operation]['end_time'] = microtime(true);
        $duration = $this->metrics[$component][$operation]['end_time'] - $this->metrics[$component][$operation]['start_time'];
        
        $this->metrics[$component][$operation]['min_duration'] = min(
            $this->metrics[$component][$operation]['min_duration'],
            $duration
        );
        
        $this->metrics[$component][$operation]['max_duration'] = max(
            $this->metrics[$component][$operation]['max_duration'],
            $duration
        );
        
        $this->metrics[$component][$operation]['total_duration'] += $duration;
        $this->metrics[$component][$operation]['count']++;
        $this->metrics[$component][$operation]['duration'] = $duration;
        
        $this->checkThreshold($component, $operation, $duration);
    }

    public function setThreshold(string $component, string $operation, float $threshold): void
    {
        if (!isset($this->thresholds[$component])) {
            $this->thresholds[$component] = [];
        }
        $this->thresholds[$component][$operation] = $threshold;
    }

    public function getMetrics(): array
    {
        return $this->metrics;
    }

    public function getComponentMetrics(string $component): array
    {
        if (!isset($this->metrics[$component])) {
            throw new \InvalidArgumentException("No metrics found for component '$component'");
        }
        return $this->metrics[$component];
    }

    public function clearMetrics(): void
    {
        $this->metrics = [];
    }

    public function getAverageDuration(string $component, string $operation): float
    {
        if (!isset($this->metrics[$component][$operation])) {
            throw new \InvalidArgumentException("No metrics found for component '$component' and operation '$operation'");
        }
        $count = $this->metrics[$component][$operation]['count'];
        return $count > 0 ? 
            $this->metrics[$component][$operation]['total_duration'] / $count : 0;
    }

    public function getMinDuration(string $component, string $operation): float
    {
        if (!isset($this->metrics[$component][$operation])) {
            throw new \InvalidArgumentException("No metrics found for component '$component' and operation '$operation'");
        }
        return $this->metrics[$component][$operation]['min_duration'] === PHP_FLOAT_MAX ? 
            0 : $this->metrics[$component][$operation]['min_duration'];
    }

    public function getMaxDuration(string $component, string $operation): float
    {
        if (!isset($this->metrics[$component][$operation])) {
            throw new \InvalidArgumentException("No metrics found for component '$component' and operation '$operation'");
        }
        return $this->metrics[$component][$operation]['max_duration'];
    }

    public function getTotalDuration(string $component, string $operation): float
    {
        if (!isset($this->metrics[$component][$operation])) {
            throw new \InvalidArgumentException("No metrics found for component '$component' and operation '$operation'");
        }
        return $this->metrics[$component][$operation]['total_duration'];
    }

    public function getMeasurementCount(string $component, string $operation): int
    {
        if (!isset($this->metrics[$component][$operation])) {
            throw new \InvalidArgumentException("No metrics found for component '$component' and operation '$operation'");
        }
        return $this->metrics[$component][$operation]['count'];
    }

    private function checkThreshold(string $component, string $operation, float $duration): void
    {
        if (isset($this->thresholds[$component][$operation]) && 
            $duration > $this->thresholds[$component][$operation]) {
            trigger_error(
                "Performance threshold exceeded for {$component}::{$operation}. " .
                "Duration: {$duration}s, Threshold: {$this->thresholds[$component][$operation]}s",
                E_USER_WARNING
            );
        }
    }
} 