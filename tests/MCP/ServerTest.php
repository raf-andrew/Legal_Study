<?php

namespace Tests\MCP;

use LegalStudy\MCP\Server;
use LegalStudy\MCP\Agent\AgentLifecycleInterface;
use LegalStudy\Initialization\InitializationStatus;
use PHPUnit\Framework\TestCase;
use Psr\Log\LoggerInterface;
use Psr\Log\NullLogger;

class ServerTest extends TestCase
{
    private Server $server;
    private LoggerInterface $logger;
    private AgentLifecycleInterface $mockAgent;

    protected function setUp(): void
    {
        $this->logger = new NullLogger();
        $this->server = new Server($this->logger, false);
        $this->mockAgent = $this->createMock(AgentLifecycleInterface::class);
    }

    public function testInitialState(): void
    {
        $this->assertTrue($this->server->isEnabled());
        $this->assertInstanceOf(InitializationStatus::class, $this->server->getStatus());
        $this->assertTrue($this->server->getStatus()->isPending());
    }

    public function testProductionEnvironment(): void
    {
        $server = new Server($this->logger, true);
        $this->assertFalse($server->isEnabled());
        
        $this->expectException(\RuntimeException::class);
        $this->expectExceptionMessage('Cannot enable MCP in production environment');
        $server->enable();
    }

    public function testEnableDisable(): void
    {
        $this->server->disable();
        $this->assertFalse($this->server->isEnabled());
        
        $this->server->enable();
        $this->assertTrue($this->server->isEnabled());
    }

    public function testAgentRegistration(): void
    {
        $this->mockAgent->method('getState')->willReturn('stopped');
        $this->mockAgent->method('getLastError')->willReturn(null);
        $this->mockAgent->method('getStatistics')->willReturn([]);
        
        $this->server->registerAgent('test-agent', $this->mockAgent);
        $this->assertSame($this->mockAgent, $this->server->getAgent('test-agent'));
        $this->assertEquals('stopped', $this->server->getAgentState('test-agent'));
        $this->assertNull($this->server->getAgentError('test-agent'));
        $this->assertEmpty($this->server->getAgentStatistics('test-agent'));
    }

    public function testAgentRegistrationWhenDisabled(): void
    {
        $this->server->disable();
        
        $this->expectException(\RuntimeException::class);
        $this->expectExceptionMessage('Cannot register agent while MCP is disabled');
        $this->server->registerAgent('test-agent', $this->mockAgent);
    }

    public function testConfiguration(): void
    {
        $config = ['security' => ['enabled' => true]];
        $this->server->setConfig($config);
        $this->assertEquals($config, $this->server->getConfig());
    }

    public function testConfigurationValidation(): void
    {
        $validConfig = ['security' => ['enabled' => true]];
        $this->assertTrue($this->server->validateConfiguration($validConfig));
        
        $invalidConfig = ['invalid' => true];
        $this->expectException(\RuntimeException::class);
        $this->server->validateConfiguration($invalidConfig);
    }

    public function testInitialization(): void
    {
        $this->mockAgent->expects($this->once())->method('initialize');
        $this->mockAgent->method('getState')->willReturn('initialized');
        $this->mockAgent->method('getLastError')->willReturn(null);
        $this->mockAgent->method('getStatistics')->willReturn([]);
        
        $this->server->registerAgent('test-agent', $this->mockAgent);
        $this->server->performInitialization();
        
        $this->assertEquals(InitializationStatus::INITIALIZED, $this->server->getStatus()->getStatus());
        $this->assertEquals('initialized', $this->server->getAgentState('test-agent'));
    }

    public function testInitializationWhenDisabled(): void
    {
        $this->server->disable();
        
        $this->expectException(\RuntimeException::class);
        $this->expectExceptionMessage('Cannot initialize MCP while disabled');
        $this->server->performInitialization();
    }

    public function testInitializationWithAgentFailure(): void
    {
        $this->mockAgent->method('initialize')->willThrowException(new \RuntimeException('Agent failed'));
        $this->mockAgent->method('getState')->willReturn('error');
        $this->mockAgent->method('getLastError')->willReturn('Agent failed');
        $this->mockAgent->method('getStatistics')->willReturn([]);
        
        $this->server->registerAgent('test-agent', $this->mockAgent);
        $this->server->performInitialization();
        
        $this->assertTrue($this->server->getStatus()->hasErrors());
        $this->assertContains('Failed to initialize agent test-agent: Agent failed', $this->server->getStatus()->getErrors());
        $this->assertEquals('error', $this->server->getAgentState('test-agent'));
        $this->assertEquals('Agent failed', $this->server->getAgentError('test-agent'));
    }

    public function testConnectionTest(): void
    {
        $this->assertTrue($this->server->testConnection());
    }

    public function testGetAgents(): void
    {
        $this->assertEmpty($this->server->getAgents());

        $agent1 = $this->createMock(AgentLifecycleInterface::class);
        $agent2 = $this->createMock(AgentLifecycleInterface::class);

        $agent1->method('getState')->willReturn('stopped');
        $agent1->method('getLastError')->willReturn(null);
        $agent1->method('getStatistics')->willReturn([]);

        $agent2->method('getState')->willReturn('stopped');
        $agent2->method('getLastError')->willReturn(null);
        $agent2->method('getStatistics')->willReturn([]);

        $this->server->registerAgent('agent1', $agent1);
        $this->server->registerAgent('agent2', $agent2);

        $agents = $this->server->getAgents();
        $this->assertCount(2, $agents);
        $this->assertSame($agent1, $agents['agent1']);
        $this->assertSame($agent2, $agents['agent2']);
    }

    public function testAgentLifecycleManagement(): void
    {
        $this->mockAgent->method('getState')->willReturnOnConsecutiveCalls(
            'stopped',
            'initialized',
            'started',
            'paused',
            'started',
            'stopped'
        );
        $this->mockAgent->method('getLastError')->willReturn(null);
        $this->mockAgent->method('getStatistics')->willReturn([]);

        $this->server->registerAgent('test-agent', $this->mockAgent);

        $this->mockAgent->expects($this->once())->method('initialize');
        $this->server->performInitialization();

        $this->mockAgent->expects($this->once())->method('start');
        $this->server->startAgent('test-agent');

        $this->mockAgent->expects($this->once())->method('pause');
        $this->server->pauseAgent('test-agent');

        $this->mockAgent->expects($this->once())->method('resume');
        $this->server->resumeAgent('test-agent');

        $this->mockAgent->expects($this->once())->method('stop');
        $this->server->stopAgent('test-agent');
    }

    public function testAgentLifecycleErrors(): void
    {
        $this->mockAgent->method('getState')->willReturn('error');
        $this->mockAgent->method('getLastError')->willReturn('Operation failed');
        $this->mockAgent->method('getStatistics')->willReturn([]);

        $this->server->registerAgent('test-agent', $this->mockAgent);

        $this->mockAgent->method('start')->willThrowException(new \RuntimeException('Start failed'));
        $this->expectException(\RuntimeException::class);
        $this->expectExceptionMessage('Start failed');
        $this->server->startAgent('test-agent');
    }

    public function testAgentNotFound(): void
    {
        $this->expectException(\RuntimeException::class);
        $this->expectExceptionMessage('Agent not found: nonexistent');
        $this->server->startAgent('nonexistent');
    }

    public function testAgentOperationsWhenDisabled(): void
    {
        $this->server->disable();

        $operations = [
            'startAgent',
            'stopAgent',
            'pauseAgent',
            'resumeAgent',
            'restartAgent'
        ];

        foreach ($operations as $operation) {
            $this->expectException(\RuntimeException::class);
            $this->expectExceptionMessage('Cannot ' . strtolower(preg_replace('/Agent$/', '', $operation)) . ' agent while MCP is disabled');
            $this->server->$operation('test-agent');
        }
    }

    public function testGetAllAgentStates(): void
    {
        $agent1 = $this->createMock(AgentLifecycleInterface::class);
        $agent2 = $this->createMock(AgentLifecycleInterface::class);

        $agent1->method('getState')->willReturn('started');
        $agent1->method('getLastError')->willReturn(null);
        $agent1->method('getStatistics')->willReturn([]);

        $agent2->method('getState')->willReturn('stopped');
        $agent2->method('getLastError')->willReturn(null);
        $agent2->method('getStatistics')->willReturn([]);

        $this->server->registerAgent('agent1', $agent1);
        $this->server->registerAgent('agent2', $agent2);

        $states = $this->server->getAllAgentStates();
        $this->assertEquals([
            'agent1' => 'started',
            'agent2' => 'stopped'
        ], $states);
    }

    public function testGetAllAgentErrors(): void
    {
        $agent1 = $this->createMock(AgentLifecycleInterface::class);
        $agent2 = $this->createMock(AgentLifecycleInterface::class);

        $agent1->method('getState')->willReturn('error');
        $agent1->method('getLastError')->willReturn('Error 1');
        $agent1->method('getStatistics')->willReturn([]);

        $agent2->method('getState')->willReturn('error');
        $agent2->method('getLastError')->willReturn('Error 2');
        $agent2->method('getStatistics')->willReturn([]);

        $this->server->registerAgent('agent1', $agent1);
        $this->server->registerAgent('agent2', $agent2);

        $errors = $this->server->getAllAgentErrors();
        $this->assertEquals([
            'agent1' => 'Error 1',
            'agent2' => 'Error 2'
        ], $errors);
    }

    public function testGetAllAgentStatistics(): void
    {
        $agent1 = $this->createMock(AgentLifecycleInterface::class);
        $agent2 = $this->createMock(AgentLifecycleInterface::class);

        $agent1->method('getState')->willReturn('started');
        $agent1->method('getLastError')->willReturn(null);
        $agent1->method('getStatistics')->willReturn(['uptime' => 100]);

        $agent2->method('getState')->willReturn('started');
        $agent2->method('getLastError')->willReturn(null);
        $agent2->method('getStatistics')->willReturn(['uptime' => 200]);

        $this->server->registerAgent('agent1', $agent1);
        $this->server->registerAgent('agent2', $agent2);

        $statistics = $this->server->getAllAgentStatistics();
        $this->assertEquals([
            'agent1' => ['uptime' => 100],
            'agent2' => ['uptime' => 200]
        ], $statistics);
    }
} 