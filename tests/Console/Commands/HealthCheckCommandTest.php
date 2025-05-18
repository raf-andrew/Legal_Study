<?php

namespace LegalStudy\Tests\Console\Commands;

use LegalStudy\Console\Commands\HealthCheckCommand;
use PHPUnit\Framework\TestCase;
use Symfony\Component\Console\Input\ArrayInput;
use Symfony\Component\Console\Output\BufferedOutput;

class HealthCheckCommandTest extends TestCase
{
    private HealthCheckCommand $command;
    private BufferedOutput $output;

    protected function setUp(): void
    {
        $this->command = new HealthCheckCommand();
        $this->output = new BufferedOutput();
    }

    public function testDefaultCheck(): void
    {
        $input = new ArrayInput([]);
        $result = $this->command->run($input, $this->output);
        $output = $this->output->fetch();

        $this->assertStringContainsString('System Health Check', $output);
        $this->assertStringContainsString('Checking database', $output);
        $this->assertStringContainsString('Checking cache', $output);
        $this->assertStringContainsString('Checking filesystem', $output);
        $this->assertStringContainsString('Checking api', $output);
        $this->assertStringContainsString('Checking security', $output);
        $this->assertTrue(in_array($result, [Command::SUCCESS, Command::FAILURE]));
    }

    public function testSpecificComponent(): void
    {
        $input = new ArrayInput(['--component' => 'database']);
        $result = $this->command->run($input, $this->output);
        $output = $this->output->fetch();

        $this->assertStringContainsString('System Health Check', $output);
        $this->assertStringContainsString('Checking database', $output);
        $this->assertStringNotContainsString('Checking cache', $output);
        $this->assertTrue(in_array($result, [Command::SUCCESS, Command::FAILURE]));
    }

    public function testVerboseOutput(): void
    {
        $input = new ArrayInput(['--verbose' => true]);
        $this->command->run($input, $this->output);
        $output = $this->output->fetch();

        $this->assertStringContainsString('Metric', $output);
        $this->assertStringContainsString('Value', $output);
        $this->assertStringContainsString('Status', $output);
        $this->assertStringContainsString('Response Time', $output);
        $this->assertStringContainsString('Error Rate', $output);
        $this->assertStringContainsString('Resource Usage', $output);
    }

    public function testCommandName(): void
    {
        $this->assertEquals('health:check', $this->command->getName());
    }

    public function testCommandDescription(): void
    {
        $this->assertEquals('Check the health of the system', $this->command->getDescription());
    }

    public function testCommandHelp(): void
    {
        $this->assertEquals(
            'This command checks the health of various system components.',
            $this->command->getHelp()
        );
    }
} 