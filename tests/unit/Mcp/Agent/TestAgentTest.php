<?php

namespace Tests\Unit\Mcp\Agent;

use App\Mcp\Agent\TestAgent;
use Tests\TestCase;

class TestAgentTest extends TestCase
{
    protected $agent;

    protected function setUp(): void
    {
        parent::setUp();
        $this->agent = new TestAgent('test-agent');
    }

    public function testAgentInitialization()
    {
        $this->assertEquals('test-agent', $this->agent->getId());
        $this->assertTrue($this->agent->hasCapability('test'));
        $this->assertTrue($this->agent->hasCapability('debug'));
        
        $metadata = $this->agent->getMetadata();
        $this->assertEquals('1.0.0', $metadata['version']);
        $this->assertEquals('Test agent for MCP system', $metadata['description']);
    }

    public function testEchoAction()
    {
        $message = 'Hello, World!';
        $result = $this->agent->execute('echo', ['message' => $message]);
        $this->assertEquals($message, $result);
    }

    public function testSumAction()
    {
        $numbers = [1, 2, 3, 4, 5];
        $result = $this->agent->execute('sum', ['numbers' => $numbers]);
        $this->assertEquals(15, $result);
    }

    public function testInvalidSumAction()
    {
        $result = $this->agent->execute('sum', ['numbers' => 'not-an-array']);
        $this->assertNull($result);
    }

    public function testStatusAction()
    {
        $state = $this->agent->execute('status');
        $this->assertIsArray($state);
    }

    public function testUnknownAction()
    {
        $result = $this->agent->execute('unknown-action');
        $this->assertNull($result);
    }

    public function testEventHandling()
    {
        $eventData = ['test' => 'data'];
        $this->agent->handleEvent('test.event', $eventData);
        
        $state = $this->agent->getState();
        $this->assertEquals($eventData, $state['last_event']);
    }

    public function testUnknownEvent()
    {
        $this->agent->handleEvent('unknown.event');
        // Should not throw an exception
        $this->assertTrue(true);
    }

    public function testStateManagement()
    {
        $state = ['key' => 'value'];
        $this->agent->setState($state);
        $this->assertEquals($state, $this->agent->getState());
    }

    public function testCapabilityManagement()
    {
        $this->agent->addCapability('new-capability');
        $this->assertTrue($this->agent->hasCapability('new-capability'));
        
        $this->agent->removeCapability('new-capability');
        $this->assertFalse($this->agent->hasCapability('new-capability'));
    }
} 