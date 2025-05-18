<?php

namespace LegalStudy\Tests\Console;

use PHPUnit\Framework\TestCase;
use LegalStudy\Console\Command;

abstract class CommandTestCase extends TestCase
{
    protected $command;
    protected $input = [];
    protected $output = [];

    protected function setUp(): void
    {
        parent::setUp();
        $this->command = $this->createCommand();
        $this->input = [];
        $this->output = [];
    }

    abstract protected function createCommand(): Command;

    protected function executeCommand(array $input = []): int
    {
        $this->input = array_merge($this->input, $input);
        return $this->command->execute($this->input, $this->output);
    }

    protected function assertCommandOutputContains(string $expected): void
    {
        $this->assertStringContainsString($expected, implode("\n", $this->output));
    }

    protected function assertCommandOutputNotContains(string $unexpected): void
    {
        $this->assertStringNotContainsString($unexpected, implode("\n", $this->output));
    }

    protected function assertCommandOutputMatches(string $pattern): void
    {
        $this->assertMatchesRegularExpression($pattern, implode("\n", $this->output));
    }

    protected function assertCommandOutputEmpty(): void
    {
        $this->assertEmpty($this->output);
    }

    protected function assertCommandOutputNotEmpty(): void
    {
        $this->assertNotEmpty($this->output);
    }

    protected function assertCommandSuccess(): void
    {
        $this->assertEquals(0, $this->executeCommand());
    }

    protected function assertCommandFailure(): void
    {
        $this->assertNotEquals(0, $this->executeCommand());
    }
} 