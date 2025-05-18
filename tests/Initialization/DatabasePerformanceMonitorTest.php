<?php

namespace Tests\Initialization;

use LegalStudy\ModularInitialization\Services\DatabasePerformanceMonitor;
use PHPUnit\Framework\TestCase;

/**
 * @covers \LegalStudy\Initialization\DatabasePerformanceMonitor
 */
class DatabasePerformanceMonitorTest extends TestCase
{
    private DatabasePerformanceMonitor $monitor;

    protected function setUp(): void
    {
        $this->monitor = new DatabasePerformanceMonitor();
    }

    public function testConnectionMeasurement(): void
    {
        $startTime = $this->monitor->startConnectionMeasurement();
        usleep(1000); // Simulate 1ms delay
        $this->monitor->endConnectionMeasurement($startTime);

        $metrics = $this->monitor->getMetrics();
        $this->assertGreaterThan(0, $metrics['avg_connection_time']);
        $this->assertEquals(1, $metrics['connection_attempts']);
    }

    public function testQueryMeasurement(): void
    {
        $startTime = $this->monitor->startQueryMeasurement();
        usleep(1000); // Simulate 1ms delay
        $this->monitor->endQueryMeasurement($startTime);

        $metrics = $this->monitor->getMetrics();
        $this->assertGreaterThan(0, $metrics['avg_query_time']);
        $this->assertEquals(1, $metrics['query_count']);
    }

    public function testTransactionMeasurement(): void
    {
        $startTime = $this->monitor->startTransactionMeasurement();
        usleep(1000); // Simulate 1ms delay
        $this->monitor->endTransactionMeasurement($startTime);

        $metrics = $this->monitor->getMetrics();
        $this->assertGreaterThan(0, $metrics['avg_transaction_time']);
        $this->assertEquals(1, $metrics['transaction_count']);
    }

    public function testRetryCount(): void
    {
        $this->monitor->incrementRetryCount();
        $this->monitor->incrementRetryCount();

        $metrics = $this->monitor->getMetrics();
        $this->assertEquals(2, $metrics['retry_count']);
    }

    public function testRollbackCount(): void
    {
        $this->monitor->incrementRollbackCount();
        $this->monitor->incrementRollbackCount();
        $this->monitor->incrementRollbackCount();

        $metrics = $this->monitor->getMetrics();
        $this->assertEquals(3, $metrics['rollback_count']);
    }

    public function testMultipleMeasurements(): void
    {
        // First measurement
        $startTime1 = $this->monitor->startConnectionMeasurement();
        usleep(1000);
        $this->monitor->endConnectionMeasurement($startTime1);

        // Second measurement
        $startTime2 = $this->monitor->startConnectionMeasurement();
        usleep(2000);
        $this->monitor->endConnectionMeasurement($startTime2);

        $metrics = $this->monitor->getMetrics();
        $this->assertGreaterThan(0, $metrics['avg_connection_time']);
        $this->assertEquals(2, $metrics['connection_attempts']);
    }

    public function testReset(): void
    {
        // Add some measurements
        $startTime = $this->monitor->startConnectionMeasurement();
        $this->monitor->endConnectionMeasurement($startTime);
        $this->monitor->incrementRetryCount();
        $this->monitor->incrementRollbackCount();

        // Reset
        $this->monitor->reset();

        // Check metrics are reset
        $metrics = $this->monitor->getMetrics();
        $this->assertEquals(0, $metrics['avg_connection_time']);
        $this->assertEquals(0, $metrics['connection_attempts']);
        $this->assertEquals(0, $metrics['retry_count']);
        $this->assertEquals(0, $metrics['rollback_count']);
    }

    public function testEmptyMetrics(): void
    {
        $metrics = $this->monitor->getMetrics();
        $this->assertEquals(0, $metrics['avg_connection_time']);
        $this->assertEquals(0, $metrics['avg_query_time']);
        $this->assertEquals(0, $metrics['avg_transaction_time']);
        $this->assertEquals(0, $metrics['retry_count']);
        $this->assertEquals(0, $metrics['transaction_count']);
        $this->assertEquals(0, $metrics['rollback_count']);
        $this->assertEquals(0, $metrics['connection_attempts']);
        $this->assertEquals(0, $metrics['query_count']);
    }
} 