<?php

namespace Tests\MCP\Agent;

use LegalStudy\MCP\Agent\AbstractAgent;
use LegalStudy\MCP\Agent\AgentLifecycleInterface;
use PHPUnit\Framework\TestCase;
use Psr\Log\LoggerInterface;
use Psr\Log\NullLogger;

class TestAgent extends AbstractAgent
{
    protected function doInitialize(): void
    {
        // No-op for testing
    }

    protected function doStart(): void
    {
        // No-op for testing
    }

    protected function doStop(): void
    {
        // No-op for testing
    }

    protected function doPause(): void
    {
        // No-op for testing
    }

    protected function doResume(): void
    {
        // No-op for testing
    }
}

class AgentLifecycleTest extends TestCase
{
    private TestAgent $agent;
    private LoggerInterface $logger;

    protected function setUp(): void
    {
        $this->logger = new NullLogger();
        $this->agent = new TestAgent($this->logger);
    }

    public function testInitialState(): void
    {
        $this->assertEquals(AgentLifecycleInterface::STATE_STOPPED, $this->agent->getState());
        $this->assertTrue($this->agent->isHealthy());
        $this->assertNull($this->agent->getLastError());
        $this->assertEquals(0, $this->agent->getUptime());
    }

    public function testInitialize(): void
    {
        $this->agent->initialize();
        $this->assertEquals(AgentLifecycleInterface::STATE_INITIALIZED, $this->agent->getState());
        $this->assertTrue($this->agent->isHealthy());
    }

    public function testStart(): void
    {
        $this->agent->initialize();
        $this->agent->start();
        usleep(1000); // Add a small delay to ensure uptime is greater than 0
        $this->assertEquals(AgentLifecycleInterface::STATE_STARTED, $this->agent->getState());
        $this->assertTrue($this->agent->isHealthy());
        $this->assertGreaterThan(0, $this->agent->getUptime());
    }

    public function testStop(): void
    {
        $this->agent->initialize();
        $this->agent->start();
        $this->agent->stop();
        $this->assertEquals(AgentLifecycleInterface::STATE_STOPPED, $this->agent->getState());
        $this->assertEquals(0, $this->agent->getUptime());
    }

    public function testPause(): void
    {
        $this->agent->initialize();
        $this->agent->start();
        $this->agent->pause();
        $this->assertEquals(AgentLifecycleInterface::STATE_PAUSED, $this->agent->getState());
    }

    public function testResume(): void
    {
        $this->agent->initialize();
        $this->agent->start();
        $this->agent->pause();
        $this->agent->resume();
        $this->assertEquals(AgentLifecycleInterface::STATE_STARTED, $this->agent->getState());
    }

    public function testRestart(): void
    {
        $this->agent->initialize();
        $this->agent->start();
        $this->agent->restart();
        $this->assertEquals(AgentLifecycleInterface::STATE_STARTED, $this->agent->getState());
    }

    public function testStartWithoutInitialization(): void
    {
        $this->expectException(\RuntimeException::class);
        $this->expectExceptionMessage('Agent must be initialized or stopped to start');
        $this->agent->start();
    }

    public function testPauseWithoutStart(): void
    {
        $this->expectException(\RuntimeException::class);
        $this->expectExceptionMessage('Agent must be started to pause');
        $this->agent->pause();
    }

    public function testResumeWithoutPause(): void
    {
        $this->expectException(\RuntimeException::class);
        $this->expectExceptionMessage('Agent must be paused to resume');
        $this->agent->resume();
    }

    public function testStopWithoutStart(): void
    {
        $this->expectException(\RuntimeException::class);
        $this->expectExceptionMessage('Agent must be started or paused to stop');
        $this->agent->stop();
    }

    public function testErrorState(): void
    {
        $failingAgent = new class($this->logger) extends TestAgent {
            protected function doInitialize(): void
            {
                throw new \RuntimeException('Test error');
            }
        };

        try {
            $failingAgent->initialize();
            $this->fail('Expected RuntimeException was not thrown');
        } catch (\RuntimeException $e) {
            $this->assertEquals('Test error', $e->getMessage());
            $this->assertEquals(AgentLifecycleInterface::STATE_ERROR, $failingAgent->getState());
            $this->assertFalse($failingAgent->isHealthy());
            $this->assertEquals('Test error', $failingAgent->getLastError());
        }
    }

    public function testStatistics(): void
    {
        $this->agent->initialize();
        $this->agent->start();
        usleep(1000); // Add a small delay to ensure uptime is greater than 0
        
        $stats = $this->agent->getStatistics();
        $this->assertArrayHasKey('state', $stats);
        $this->assertArrayHasKey('uptime', $stats);
        $this->assertArrayHasKey('last_error', $stats);
        $this->assertArrayHasKey('is_healthy', $stats);
        
        $this->assertEquals(AgentLifecycleInterface::STATE_STARTED, $stats['state']);
        $this->assertGreaterThan(0, $stats['uptime']);
        $this->assertNull($stats['last_error']);
        $this->assertTrue($stats['is_healthy']);
    }
} 