<?php

namespace LegalStudy\Initialization;

class InitializationPerformanceMonitor
{
    private array $measurements = [];
    private array $metrics = [];

    public function startMeasurement(string $operation): void
    {
        $this->measurements[$operation] = [
            'start' => microtime(true),
            'memory_start' => memory_get_usage(true),
            'end' => null,
            'memory_end' => null,
            'duration' => null,
            'memory_peak' => null
        ];
    }

    public function endMeasurement(string $operation): void
    {
        if (isset($this->measurements[$operation])) {
            $this->measurements[$operation]['end'] = microtime(true);
            $this->measurements[$operation]['memory_end'] = memory_get_usage(true);
            $this->measurements[$operation]['memory_peak'] = memory_get_peak_usage(true);
            $this->measurements[$operation]['duration'] = 
                $this->measurements[$operation]['end'] - $this->measurements[$operation]['start'];
            
            $this->updateMetrics($operation);
        }
    }

    public function getMeasurements(): array
    {
        return $this->measurements;
    }

    public function getMetrics(): array
    {
        return $this->metrics;
    }

    private function updateMetrics(string $operation): void
    {
        $measurement = $this->measurements[$operation];
        
        $this->metrics[$operation] = [
            'duration' => $measurement['duration'],
            'memory_usage' => $measurement['memory_end'] - $measurement['memory_start'],
            'memory_peak' => $measurement['memory_peak']
        ];
    }

    public function reset(): void
    {
        $this->measurements = [];
        $this->metrics = [];
    }
} 