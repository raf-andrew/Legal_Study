<?php

namespace LegalStudy\Console\Tests;

use LegalStudy\Console\Commands\HealthCheckCommand;
use PHPUnit\Framework\TestCase;

class HealthCheckCommandTest extends TestCase
{
    private HealthCheckCommand $command;

    protected function setUp(): void
    {
        $this->command = new HealthCheckCommand();
    }

    public function testCommandName()
    {
        $this->assertEquals('health:check', $this->command->getName());
    }

    public function testCommandDescription()
    {
        $this->assertNotEmpty($this->command->getDescription());
    }

    public function testHelpText()
    {
        $help = $this->command->getHelp();
        $this->assertStringContainsString('Command: health:check', $help);
        $this->assertStringContainsString('Description:', $help);
        $this->assertStringContainsString('Optional Arguments:', $help);
    }

    public function testValidateArguments()
    {
        $this->assertTrue($this->command->validateArguments([]));
        $this->assertTrue($this->command->validateArguments(['component' => 'database']));
        $this->assertTrue($this->command->validateArguments(['verbose' => true]));
    }

    public function testExecuteWithNoArguments()
    {
        $result = $this->command->execute([]);
        $this->assertEquals(0, $result);
    }

    public function testExecuteWithComponent()
    {
        $result = $this->command->execute(['component' => 'database']);
        $this->assertEquals(0, $result);
    }

    public function testExecuteWithVerbose()
    {
        $result = $this->command->execute(['verbose' => true]);
        $this->assertEquals(0, $result);
    }

    public function testExecuteWithInvalidComponent()
    {
        $result = $this->command->execute(['component' => 'invalid']);
        $this->assertEquals(0, $result); // Should still return success as invalid components are ignored
    }
} 