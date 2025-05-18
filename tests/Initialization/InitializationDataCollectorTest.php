<?php

namespace Tests\Initialization;

use LegalStudy\ModularInitialization\Services\InitializationDataCollector;
use PHPUnit\Framework\TestCase;

class InitializationDataCollectorTest extends TestCase
{
    private InitializationDataCollector $collector;

    protected function setUp(): void
    {
        $this->collector = new InitializationDataCollector();
    }

    public function testCollectData(): void
    {
        $this->collector->collectData('test', 'key1', 'value1');
        $this->collector->collectData('test', 'key2', 'value2');

        $this->assertEquals('value1', $this->collector->getData('test', 'key1'));
        $this->assertEquals('value2', $this->collector->getData('test', 'key2'));
        $this->assertEquals(['key1' => 'value1', 'key2' => 'value2'], $this->collector->getData('test'));
    }

    public function testCollectMetric(): void
    {
        $this->collector->collectMetric('test', 'metric1', 1.5);
        $this->collector->collectMetric('test', 'metric2', 2.5);

        $this->assertEquals(1.5, $this->collector->getMetrics('test', 'metric1'));
        $this->assertEquals(2.5, $this->collector->getMetrics('test', 'metric2'));
        $this->assertEquals(['metric1' => 1.5, 'metric2' => 2.5], $this->collector->getMetrics('test'));
    }

    public function testTimerOperations(): void
    {
        $this->collector->startTimer('test', 'operation');
        usleep(1000); // Sleep for 1ms
        $duration = $this->collector->stopTimer('test', 'operation');

        $this->assertGreaterThan(0, $duration);
        $timerData = $this->collector->getTimerData('test', 'operation');
        $this->assertNotNull($timerData);
        $this->assertArrayHasKey('start', $timerData);
        $this->assertArrayHasKey('end', $timerData);
        $this->assertGreaterThan($timerData['start'], $timerData['end']);
    }

    public function testStopTimerWithoutStart(): void
    {
        $this->expectException(\RuntimeException::class);
        $this->collector->stopTimer('test', 'operation');
    }

    public function testGetNonExistentData(): void
    {
        $this->assertNull($this->collector->getData('non_existent'));
        $this->assertNull($this->collector->getData('test', 'non_existent'));
    }

    public function testGetNonExistentMetrics(): void
    {
        $this->assertNull($this->collector->getMetrics('non_existent'));
        $this->assertNull($this->collector->getMetrics('test', 'non_existent'));
    }

    public function testGetAllData(): void
    {
        $this->collector->collectData('test', 'key', 'value');
        $this->collector->collectMetric('test', 'metric', 1.5);
        $this->collector->startTimer('test', 'operation');
        $this->collector->stopTimer('test', 'operation');

        $allData = $this->collector->getAllData();
        $this->assertArrayHasKey('data', $allData);
        $this->assertArrayHasKey('metrics', $allData);
        $this->assertArrayHasKey('timestamps', $allData);
    }

    public function testClearData(): void
    {
        $this->collector->collectData('test', 'key', 'value');
        $this->collector->collectMetric('test', 'metric', 1.5);
        $this->collector->startTimer('test', 'operation');
        $this->collector->stopTimer('test', 'operation');

        $this->collector->clearData();

        $this->assertEmpty($this->collector->getData('test'));
        $this->assertEmpty($this->collector->getMetrics('test'));
        $this->assertNull($this->collector->getTimerData('test', 'operation'));
    }

    public function testMultipleComponents(): void
    {
        $this->collector->collectData('component1', 'key', 'value1');
        $this->collector->collectData('component2', 'key', 'value2');

        $this->assertEquals('value1', $this->collector->getData('component1', 'key'));
        $this->assertEquals('value2', $this->collector->getData('component2', 'key'));
    }

    public function testTimerKeyGeneration(): void
    {
        $this->collector->startTimer('component', 'operation');
        $timerData = $this->collector->getTimerData('component', 'operation');
        $this->assertNotNull($timerData);
    }
} 