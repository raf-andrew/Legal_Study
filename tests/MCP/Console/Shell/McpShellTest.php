<?php

namespace Tests\Mcp\Console\Shell;

use Mcp\Console\Shell\McpShell;
use Tests\TestCase;
use Illuminate\Support\Facades\Artisan;
use Symfony\Component\Console\Input\ArrayInput;
use Symfony\Component\Console\Output\BufferedOutput;
use Mockery;

class McpShellTest extends TestCase
{
    private McpShell $shell;
    private BufferedOutput $output;

    protected function setUp(): void
    {
        parent::setUp();
        
        $this->shell = new McpShell();
        $this->output = new BufferedOutput();
        
        $this->shell->setOutput($this->output);
    }

    public function testShellWelcomeMessage(): void
    {
        $this->shell->execute(new ArrayInput([]), $this->output);
        
        $output = $this->output->fetch();
        
        $this->assertStringContainsString('Welcome to the MCP Interactive Shell', $output);
        $this->assertStringContainsString('Type "help" for a list of commands', $output);
    }

    public function testHelpCommand(): void
    {
        $this->shell->execute(new ArrayInput([]), $this->output);
        
        $output = $this->output->fetch();
        
        $this->assertStringContainsString('Built-in Commands:', $output);
        $this->assertStringContainsString('Custom Commands:', $output);
        $this->assertStringContainsString('Defined Aliases:', $output);
        $this->assertStringContainsString('Available Artisan Commands:', $output);
    }

    public function testHistoryCommand(): void
    {
        $this->shell->processCommand('help');
        $this->shell->processCommand('status');
        $this->shell->processCommand('history');
        
        $output = $this->output->fetch();
        
        $this->assertStringContainsString('Command History:', $output);
        $this->assertStringContainsString('help', $output);
        $this->assertStringContainsString('status', $output);
    }

    public function testAliasCommand(): void
    {
        $this->shell->processCommand('alias test=help');
        
        $output = $this->output->fetch();
        
        $this->assertStringContainsString('Alias defined: test -> help', $output);
        
        $this->output->fetch(); // Clear output
        
        $this->shell->processCommand('test');
        
        $output = $this->output->fetch();
        $this->assertStringContainsString('Built-in Commands:', $output);
    }

    public function testInvalidAliasDefinition(): void
    {
        $this->shell->processCommand('alias invalid');
        
        $output = $this->output->fetch();
        
        $this->assertStringContainsString('Invalid alias definition', $output);
    }

    public function testCustomCommands(): void
    {
        Artisan::shouldReceive('call')
            ->once()
            ->with('mcp:agents', [], Mockery::any());

        $this->shell->processCommand('agents');
    }

    public function testPredefinedAliases(): void
    {
        Artisan::shouldReceive('call')
            ->once()
            ->with('list', [], Mockery::any());

        $this->shell->processCommand('ll');
    }

    public function testClearCommand(): void
    {
        $this->shell->processCommand('clear');
        
        $output = $this->output->fetch();
        
        $this->assertEquals("\033[H\033[2J", $output);
    }

    public function testInvalidCommand(): void
    {
        Artisan::shouldReceive('call')
            ->once()
            ->with('invalid-command', [], Mockery::any())
            ->andThrow(new \Exception('Command not found'));

        $this->shell->processCommand('invalid-command');
        
        $output = $this->output->fetch();
        
        $this->assertStringContainsString('Error executing command: Command not found', $output);
    }

    public function testEmptyCommand(): void
    {
        $this->shell->processCommand('');
        
        $output = $this->output->fetch();
        
        $this->assertEmpty($output);
    }

    public function testAutocomplete(): void
    {
        $autocompleteValues = $this->shell->getAutocompleteValues();
        
        $this->assertContains('help', $autocompleteValues);
        $this->assertContains('exit', $autocompleteValues);
        $this->assertContains('history', $autocompleteValues);
        $this->assertContains('alias', $autocompleteValues);
        $this->assertContains('agents', $autocompleteValues);
        $this->assertContains('tasks', $autocompleteValues);
        $this->assertContains('discover', $autocompleteValues);
        $this->assertContains('monitor', $autocompleteValues);
        $this->assertContains('status', $autocompleteValues);
        $this->assertContains('clear', $autocompleteValues);
        $this->assertContains('ll', $autocompleteValues);
        $this->assertContains('ps', $autocompleteValues);
        $this->assertContains('cls', $autocompleteValues);
    }
} 