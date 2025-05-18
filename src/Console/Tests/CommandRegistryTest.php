<?php

namespace LegalStudy\Console\Tests;

use LegalStudy\Console\CommandRegistry;
use LegalStudy\Console\Commands\HealthCheckCommand;
use PHPUnit\Framework\TestCase;

class CommandRegistryTest extends TestCase
{
    private CommandRegistry $registry;
    private HealthCheckCommand $healthCheckCommand;

    protected function setUp(): void
    {
        $this->registry = new CommandRegistry();
        $this->healthCheckCommand = new HealthCheckCommand();
    }

    public function testRegisterCommand()
    {
        $this->registry->register($this->healthCheckCommand);
        $this->assertTrue($this->registry->hasCommand('health:check'));
    }

    public function testGetCommand()
    {
        $this->registry->register($this->healthCheckCommand);
        $command = $this->registry->getCommand('health:check');
        $this->assertInstanceOf(HealthCheckCommand::class, $command);
    }

    public function testGetNonExistentCommand()
    {
        $command = $this->registry->getCommand('nonexistent');
        $this->assertNull($command);
    }

    public function testGetCommands()
    {
        $this->registry->register($this->healthCheckCommand);
        $commands = $this->registry->getCommands();
        $this->assertCount(1, $commands);
        $this->assertArrayHasKey('health:check', $commands);
    }

    public function testGetCommandHelp()
    {
        $this->registry->register($this->healthCheckCommand);
        $help = $this->registry->getCommandHelp('health:check');
        $this->assertNotNull($help);
        $this->assertStringContainsString('Command: health:check', $help);
    }

    public function testGetNonExistentCommandHelp()
    {
        $help = $this->registry->getCommandHelp('nonexistent');
        $this->assertNull($help);
    }

    public function testExecuteCommand()
    {
        $this->registry->register($this->healthCheckCommand);
        $result = $this->registry->executeCommand('health:check', []);
        $this->assertEquals(0, $result);
    }

    public function testExecuteNonExistentCommand()
    {
        $this->expectException(\InvalidArgumentException::class);
        $this->registry->executeCommand('nonexistent', []);
    }

    public function testRemoveCommand()
    {
        $this->registry->register($this->healthCheckCommand);
        $this->registry->removeCommand('health:check');
        $this->assertFalse($this->registry->hasCommand('health:check'));
    }
} 