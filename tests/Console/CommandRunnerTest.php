<?php

namespace LegalStudy\Tests\Console;

use PHPUnit\Framework\TestCase;
use LegalStudy\Console\CommandRegistry;
use LegalStudy\Console\CommandRunner;
use LegalStudy\Console\Commands\HealthCheckCommand;

class CommandRunnerTest extends TestCase
{
    private $registry;
    private $runner;

    protected function setUp(): void
    {
        parent::setUp();
        $this->registry = new CommandRegistry();
        $this->runner = new CommandRunner($this->registry);
    }

    public function testRunExistingCommand(): void
    {
        $this->registry->register(new HealthCheckCommand());
        $result = $this->runner->run('health:check');
        
        $this->assertEquals(0, $result);
        $output = $this->runner->getOutput();
        $this->assertNotEmpty($output);
        $this->assertStringContainsString('System Health Status:', implode("\n", $output));
    }

    public function testRunNonExistentCommand(): void
    {
        $result = $this->runner->run('nonexistent:command');
        
        $this->assertEquals(1, $result);
        $output = $this->runner->getOutput();
        $this->assertStringContainsString("Command 'nonexistent:command' not found.", implode("\n", $output));
    }

    public function testListCommands(): void
    {
        $this->registry->register(new HealthCheckCommand());
        $commands = $this->runner->listCommands();
        
        $this->assertArrayHasKey('health:check', $commands);
        $this->assertEquals('Check the health of the system', $commands['health:check']);
    }

    public function testGetCommandHelp(): void
    {
        $this->registry->register(new HealthCheckCommand());
        $help = $this->runner->getCommandHelp('health:check');
        
        $this->assertNotNull($help);
        $this->assertStringContainsString('This command checks the health of various system components', $help);
    }

    public function testGetNonExistentCommandHelp(): void
    {
        $help = $this->runner->getCommandHelp('nonexistent:command');
        $this->assertNull($help);
    }

    public function testClearOutput(): void
    {
        $this->registry->register(new HealthCheckCommand());
        $this->runner->run('health:check');
        
        $this->assertNotEmpty($this->runner->getOutput());
        $this->runner->clearOutput();
        $this->assertEmpty($this->runner->getOutput());
    }
} 