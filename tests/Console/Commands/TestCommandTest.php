<?php

namespace LegalStudy\Tests\Console\Commands;

use LegalStudy\Console\Commands\TestCommand;
use PHPUnit\Framework\TestCase;
use Symfony\Component\Console\Input\ArrayInput;
use Symfony\Component\Console\Output\BufferedOutput;

class TestCommandTest extends TestCase
{
    private TestCommand $command;
    private BufferedOutput $output;

    protected function setUp(): void
    {
        $this->command = new TestCommand();
        $this->output = new BufferedOutput();
    }

    public function testDefaultMessage(): void
    {
        $input = new ArrayInput([]);
        $this->command->run($input, $this->output);
        $this->assertEquals("Hello, World!\n", $this->output->fetch());
    }

    public function testCustomMessage(): void
    {
        $input = new ArrayInput(['message' => 'Custom Message']);
        $this->command->run($input, $this->output);
        $this->assertEquals("Custom Message\n", $this->output->fetch());
    }

    public function testUppercaseOption(): void
    {
        $input = new ArrayInput([
            'message' => 'Custom Message',
            '--uppercase' => true
        ]);
        $this->command->run($input, $this->output);
        $this->assertEquals("CUSTOM MESSAGE\n", $this->output->fetch());
    }

    public function testCommandName(): void
    {
        $this->assertEquals('test', $this->command->getName());
    }

    public function testCommandDescription(): void
    {
        $this->assertEquals('Test command for demonstration', $this->command->getDescription());
    }

    public function testCommandHelp(): void
    {
        $this->assertEquals(
            'This is a test command to demonstrate the command infrastructure.',
            $this->command->getHelp()
        );
    }
} 