<?php

namespace LegalStudy\Initialization;

class DatabasePerformanceMonitor
{
    private array $metrics = [
        'connection_time' => [],
        'query_time' => [],
        'transaction_time' => [],
        'retry_count' => 0,
        'transaction_count' => 0,
        'rollback_count' => 0,
    ];

    public function startConnectionMeasurement(): float
    {
        return microtime(true);
    }

    public function endConnectionMeasurement(float $startTime): void
    {
        $this->metrics['connection_time'][] = microtime(true) - $startTime;
    }

    public function startQueryMeasurement(): float
    {
        return microtime(true);
    }

    public function endQueryMeasurement(float $startTime): void
    {
        $this->metrics['query_time'][] = microtime(true) - $startTime;
    }

    public function startTransactionMeasurement(): float
    {
        $this->metrics['transaction_count']++;
        return microtime(true);
    }

    public function endTransactionMeasurement(float $startTime): void
    {
        $this->metrics['transaction_time'][] = microtime(true) - $startTime;
    }

    public function incrementRetryCount(): void
    {
        $this->metrics['retry_count']++;
    }

    public function incrementRollbackCount(): void
    {
        $this->metrics['rollback_count']++;
    }

    public function getMetrics(): array
    {
        return [
            'avg_connection_time' => $this->calculateAverage($this->metrics['connection_time']),
            'avg_query_time' => $this->calculateAverage($this->metrics['query_time']),
            'avg_transaction_time' => $this->calculateAverage($this->metrics['transaction_time']),
            'retry_count' => $this->metrics['retry_count'],
            'transaction_count' => $this->metrics['transaction_count'],
            'rollback_count' => $this->metrics['rollback_count'],
            'connection_attempts' => count($this->metrics['connection_time']),
            'query_count' => count($this->metrics['query_time']),
        ];
    }

    private function calculateAverage(array $times): float
    {
        if (empty($times)) {
            return 0.0;
        }
        return array_sum($times) / count($times);
    }

    public function reset(): void
    {
        $this->metrics = [
            'connection_time' => [],
            'query_time' => [],
            'transaction_time' => [],
            'retry_count' => 0,
            'transaction_count' => 0,
            'rollback_count' => 0,
        ];
    }
} 