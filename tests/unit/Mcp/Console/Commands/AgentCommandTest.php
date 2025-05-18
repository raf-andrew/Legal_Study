<?php

namespace Tests\Unit\Mcp\Console\Commands;

use App\Mcp\Agent\Registry;
use App\Mcp\Agent\TestAgent;
use App\Mcp\Console\Commands\AgentCommand;
use App\Mcp\Server;
use Illuminate\Support\Facades\Artisan;
use Tests\TestCase;

class AgentCommandTest extends TestCase
{
    protected $server;
    protected $registry;
    protected $command;
    protected $agent;

    protected function setUp(): void
    {
        parent::setUp();

        $this->server = $this->createMock(Server::class);
        $this->registry = new Registry();
        $this->agent = new TestAgent('test-agent');

        $this->server->method('isEnabled')->willReturn(true);
        $this->server->method('getService')->with(Registry::class)->willReturn($this->registry);

        $this->app->instance(Server::class, $this->server);
        $this->registry->register($this->agent);
    }

    public function testListAgents()
    {
        $exitCode = $this->artisan('mcp:agent', [
            'action' => 'list',
            '--format' => 'json'
        ]);

        $this->assertEquals(0, $exitCode);
        $this->assertStringContainsString('test-agent', Artisan::output());
    }

    public function testListAgentsWithCapability()
    {
        $exitCode = $this->artisan('mcp:agent', [
            'action' => 'list',
            '--capability' => 'test',
            '--format' => 'json'
        ]);

        $this->assertEquals(0, $exitCode);
        $this->assertStringContainsString('test-agent', Artisan::output());
    }

    public function testShowAgentInfo()
    {
        $exitCode = $this->artisan('mcp:agent', [
            'action' => 'info',
            'agent' => 'test-agent',
            '--format' => 'json'
        ]);

        $this->assertEquals(0, $exitCode);
        $output = Artisan::output();
        $this->assertStringContainsString('test-agent', $output);
        $this->assertStringContainsString('test', $output);
        $this->assertStringContainsString('debug', $output);
    }

    public function testShowAgentInfoNotFound()
    {
        $exitCode = $this->artisan('mcp:agent', [
            'action' => 'info',
            'agent' => 'nonexistent-agent',
            '--format' => 'json'
        ]);

        $this->assertEquals(1, $exitCode);
        $this->assertStringContainsString('not found', Artisan::output());
    }

    public function testUnregisterAgent()
    {
        $exitCode = $this->artisan('mcp:agent', [
            'action' => 'unregister',
            'agent' => 'test-agent',
            '--force' => true
        ]);

        $this->assertEquals(0, $exitCode);
        $this->assertNull($this->registry->getAgent('test-agent'));
    }

    public function testExecuteAgentAction()
    {
        $exitCode = $this->artisan('mcp:agent', [
            'action' => 'execute',
            'agent' => 'test-agent',
            '--action' => 'echo',
            '--params' => json_encode(['message' => 'Hello, World!']),
            '--format' => 'json'
        ]);

        $this->assertEquals(0, $exitCode);
        $this->assertStringContainsString('Hello, World!', Artisan::output());
    }

    public function testExecuteAgentActionInvalidParams()
    {
        $exitCode = $this->artisan('mcp:agent', [
            'action' => 'execute',
            'agent' => 'test-agent',
            '--action' => 'sum',
            '--params' => json_encode(['numbers' => 'not-an-array']),
            '--format' => 'json'
        ]);

        $this->assertEquals(1, $exitCode);
    }

    public function testUnknownAction()
    {
        $exitCode = $this->artisan('mcp:agent', [
            'action' => 'unknown-action'
        ]);

        $this->assertEquals(1, $exitCode);
        $this->assertStringContainsString('Unknown action', Artisan::output());
    }
} 