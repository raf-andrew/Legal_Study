<?php

namespace Tests\Initialization;

use LegalStudy\Initialization\InitializationPerformanceMonitor;
use PHPUnit\Framework\TestCase;

/**
 * @covers \LegalStudy\Initialization\InitializationPerformanceMonitor
 */
class InitializationPerformanceMonitorTest extends TestCase
{
    private InitializationPerformanceMonitor $monitor;

    protected function setUp(): void
    {
        $this->monitor = new InitializationPerformanceMonitor();
    }

    public function testStartAndEndMeasurement(): void
    {
        $this->monitor->startMeasurement('test_operation');
        usleep(1000); // Simulate some work
        $this->monitor->endMeasurement('test_operation');

        $measurements = $this->monitor->getMeasurements();
        $metrics = $this->monitor->getMetrics();

        $this->assertArrayHasKey('test_operation', $measurements);
        $this->assertArrayHasKey('test_operation', $metrics);
        $this->assertGreaterThan(0, $measurements['test_operation']['duration']);
        $this->assertGreaterThan(0, $metrics['test_operation']['duration']);
    }

    public function testMultipleMeasurements(): void
    {
        $operations = ['op1', 'op2', 'op3'];

        foreach ($operations as $operation) {
            $this->monitor->startMeasurement($operation);
            usleep(1000); // Simulate some work
            $this->monitor->endMeasurement($operation);
        }

        $measurements = $this->monitor->getMeasurements();
        $metrics = $this->monitor->getMetrics();

        foreach ($operations as $operation) {
            $this->assertArrayHasKey($operation, $measurements);
            $this->assertArrayHasKey($operation, $metrics);
            $this->assertGreaterThan(0, $measurements[$operation]['duration']);
            $this->assertGreaterThan(0, $metrics[$operation]['duration']);
        }
    }

    public function testMemoryMeasurements(): void
    {
        $data = [];
        $this->monitor->startMeasurement('memory_test');
        for ($i = 0; $i < 10000; $i++) {
            $data[] = str_repeat('a', 100);
        }
        $this->monitor->endMeasurement('memory_test');

        $measurements = $this->monitor->getMeasurements();
        $metrics = $this->monitor->getMetrics();

        $this->assertArrayHasKey('memory_test', $measurements);
        $this->assertArrayHasKey('memory_test', $metrics);
        $this->assertGreaterThan(0, $measurements['memory_test']['memory_peak']);
        $this->assertGreaterThan(0, $metrics['memory_test']['memory_usage']);
    }

    public function testReset(): void
    {
        $this->monitor->startMeasurement('test');
        $this->monitor->endMeasurement('test');

        $this->assertNotEmpty($this->monitor->getMeasurements());
        $this->assertNotEmpty($this->monitor->getMetrics());

        $this->monitor->reset();

        $this->assertEmpty($this->monitor->getMeasurements());
        $this->assertEmpty($this->monitor->getMetrics());
    }

    public function testEndMeasurementWithoutStart(): void
    {
        $this->monitor->endMeasurement('nonexistent');
        $this->assertEmpty($this->monitor->getMeasurements());
        $this->assertEmpty($this->monitor->getMetrics());
    }

    public function testMetricsCalculation(): void
    {
        $this->monitor->startMeasurement('calc_test');
        usleep(1000); // Simulate some work
        $this->monitor->endMeasurement('calc_test');

        $metrics = $this->monitor->getMetrics();
        $this->assertArrayHasKey('calc_test', $metrics);
        $this->assertArrayHasKey('duration', $metrics['calc_test']);
        $this->assertArrayHasKey('memory_usage', $metrics['calc_test']);
        $this->assertArrayHasKey('memory_peak', $metrics['calc_test']);
    }

    public function testGetComponentMetrics(): void
    {
        $this->monitor->startMeasurement('Component1', 'operation1');
        usleep(1000);
        $this->monitor->endMeasurement('Component1', 'operation1');

        $this->monitor->startMeasurement('Component2', 'operation1');
        usleep(1000);
        $this->monitor->endMeasurement('Component2', 'operation1');

        $metrics = $this->monitor->getComponentMetrics('Component1');
        $this->assertArrayHasKey('operation1', $metrics);
        $this->assertGreaterThan(0, $metrics['operation1']['duration']);
    }

    public function testClearMetrics(): void
    {
        $this->monitor->startMeasurement('TestComponent', 'operation');
        usleep(1000);
        $this->monitor->endMeasurement('TestComponent', 'operation');

        $this->monitor->clearMetrics();
        $this->assertEmpty($this->monitor->getMetrics());
    }

    public function testGetAverageDuration(): void
    {
        $this->monitor->startMeasurement('TestComponent', 'operation');
        usleep(1000);
        $this->monitor->endMeasurement('TestComponent', 'operation');

        $this->monitor->startMeasurement('TestComponent', 'operation');
        usleep(1000);
        $this->monitor->endMeasurement('TestComponent', 'operation');

        $average = $this->monitor->getAverageDuration('TestComponent', 'operation');
        $this->assertGreaterThan(0, $average);
    }

    public function testGetMinMaxDuration(): void
    {
        $this->monitor->startMeasurement('TestComponent', 'operation');
        usleep(1000);
        $this->monitor->endMeasurement('TestComponent', 'operation');

        $this->monitor->startMeasurement('TestComponent', 'operation');
        usleep(2000);
        $this->monitor->endMeasurement('TestComponent', 'operation');

        $minDuration = $this->monitor->getMinDuration('TestComponent', 'operation');
        $maxDuration = $this->monitor->getMaxDuration('TestComponent', 'operation');
        
        $this->assertGreaterThan(0, $minDuration);
        $this->assertGreaterThan($minDuration, $maxDuration);
    }

    public function testGetTotalDuration(): void
    {
        $this->monitor->startMeasurement('TestComponent', 'operation');
        usleep(1000);
        $this->monitor->endMeasurement('TestComponent', 'operation');

        $this->monitor->startMeasurement('TestComponent', 'operation');
        usleep(1000);
        $this->monitor->endMeasurement('TestComponent', 'operation');

        $total = $this->monitor->getTotalDuration('TestComponent', 'operation');
        $this->assertGreaterThan(0, $total);
    }

    public function testGetMeasurementCount(): void
    {
        $this->monitor->startMeasurement('TestComponent', 'operation');
        usleep(1000);
        $this->monitor->endMeasurement('TestComponent', 'operation');

        $this->monitor->startMeasurement('TestComponent', 'operation');
        usleep(1000);
        $this->monitor->endMeasurement('TestComponent', 'operation');

        $count = $this->monitor->getMeasurementCount('TestComponent', 'operation');
        $this->assertEquals(2, $count);
    }

    public function testInvalidComponent(): void
    {
        $this->expectException(\InvalidArgumentException::class);
        $this->monitor->getComponentMetrics('NonExistentComponent');
    }

    public function testInvalidOperation(): void
    {
        $this->monitor->startMeasurement('TestComponent', 'operation');
        $this->monitor->endMeasurement('TestComponent', 'operation');

        $this->expectException(\InvalidArgumentException::class);
        $this->monitor->getAverageDuration('TestComponent', 'nonexistent');
    }
} 