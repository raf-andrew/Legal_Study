<?php

namespace Tests\Unit\Mcp\Agent;

use App\Mcp\Agent\Registry;
use App\Mcp\Agent\TestAgent;
use Tests\TestCase;

class RegistryTest extends TestCase
{
    protected $registry;
    protected $agent;

    protected function setUp(): void
    {
        parent::setUp();
        
        $this->registry = new Registry();
        $this->agent = new TestAgent('test-agent');
    }

    public function testAgentRegistration()
    {
        $result = $this->registry->register($this->agent);
        $this->assertTrue($result);
        
        $registeredAgent = $this->registry->getAgent('test-agent');
        $this->assertNotNull($registeredAgent);
        $this->assertEquals('test-agent', $registeredAgent->getId());
    }

    public function testDuplicateRegistration()
    {
        $this->registry->register($this->agent);
        $result = $this->registry->register($this->agent);
        $this->assertFalse($result);
    }

    public function testAgentUnregistration()
    {
        $this->registry->register($this->agent);
        $result = $this->registry->unregister('test-agent');
        $this->assertTrue($result);
        
        $unregisteredAgent = $this->registry->getAgent('test-agent');
        $this->assertNull($unregisteredAgent);
    }

    public function testNonexistentAgentUnregistration()
    {
        $result = $this->registry->unregister('nonexistent-agent');
        $this->assertFalse($result);
    }

    public function testCapabilityManagement()
    {
        $this->registry->register($this->agent);
        
        $capabilities = $this->registry->getCapabilities();
        $this->assertArrayHasKey('test', $capabilities);
        $this->assertArrayHasKey('debug', $capabilities);
        
        $agentsWithTest = $this->registry->getAgentsWithCapability('test');
        $this->assertCount(1, $agentsWithTest);
        $this->assertEquals('test-agent', $agentsWithTest->first()->getId());
    }

    public function testAgentValidation()
    {
        $errors = $this->registry->validateAgent($this->agent);
        $this->assertEmpty($errors);
    }

    public function testInvalidAgentValidation()
    {
        $invalidAgent = new class {
            public function getId() { return ''; }
            public function getCapabilities() { return []; }
            public function hasCapability($capability) { return false; }
            public function execute($action, $parameters = []) { return null; }
        };

        $errors = $this->registry->validateAgent($invalidAgent);
        $this->assertNotEmpty($errors);
        $this->assertContains('Agent ID is required', $errors);
        $this->assertContains('Agent must have at least one capability', $errors);
    }

    public function testAgentCollection()
    {
        $this->registry->register($this->agent);
        $agents = $this->registry->getAgents();
        
        $this->assertCount(1, $agents);
        $this->assertEquals('test-agent', $agents->first()->getId());
    }
} 