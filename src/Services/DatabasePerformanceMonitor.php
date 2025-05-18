<?php

namespace LegalStudy\ModularInitialization\Services;

class DatabasePerformanceMonitor
{
    private array $metrics = [
        'connections' => ['count' => 0, 'total_time' => 0.0],
        'queries' => ['count' => 0, 'total_time' => 0.0],
        'transactions' => ['count' => 0, 'total_time' => 0.0],
        'retries' => ['count' => 0],
        'rollbacks' => ['count' => 0]
    ];

    private array $currentMeasurements = [];

    public function startConnectionMeasurement(): void
    {
        $this->currentMeasurements['connection'] = microtime(true);
    }

    public function endConnectionMeasurement(): void
    {
        if (!isset($this->currentMeasurements['connection'])) {
            throw new \RuntimeException('No connection measurement started');
        }

        $duration = microtime(true) - $this->currentMeasurements['connection'];
        $this->metrics['connections']['count']++;
        $this->metrics['connections']['total_time'] += $duration;
        unset($this->currentMeasurements['connection']);
    }

    public function startQueryMeasurement(): void
    {
        $this->currentMeasurements['query'] = microtime(true);
    }

    public function endQueryMeasurement(): void
    {
        if (!isset($this->currentMeasurements['query'])) {
            throw new \RuntimeException('No query measurement started');
        }

        $duration = microtime(true) - $this->currentMeasurements['query'];
        $this->metrics['queries']['count']++;
        $this->metrics['queries']['total_time'] += $duration;
        unset($this->currentMeasurements['query']);
    }

    public function startTransactionMeasurement(): void
    {
        $this->currentMeasurements['transaction'] = microtime(true);
    }

    public function endTransactionMeasurement(): void
    {
        if (!isset($this->currentMeasurements['transaction'])) {
            throw new \RuntimeException('No transaction measurement started');
        }

        $duration = microtime(true) - $this->currentMeasurements['transaction'];
        $this->metrics['transactions']['count']++;
        $this->metrics['transactions']['total_time'] += $duration;
        unset($this->currentMeasurements['transaction']);
    }

    public function incrementRetryCount(): void
    {
        $this->metrics['retries']['count']++;
    }

    public function incrementRollbackCount(): void
    {
        $this->metrics['rollbacks']['count']++;
    }

    public function getMetrics(string $type = null): array
    {
        if ($type === null) {
            return $this->metrics;
        }

        if (!isset($this->metrics[$type])) {
            throw new \InvalidArgumentException("Invalid metric type: {$type}");
        }

        return $this->metrics[$type];
    }

    public function reset(): void
    {
        $this->metrics = [
            'connections' => ['count' => 0, 'total_time' => 0.0],
            'queries' => ['count' => 0, 'total_time' => 0.0],
            'transactions' => ['count' => 0, 'total_time' => 0.0],
            'retries' => ['count' => 0],
            'rollbacks' => ['count' => 0]
        ];
        $this->currentMeasurements = [];
    }
} 