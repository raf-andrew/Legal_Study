<?php

namespace LegalStudy\Tests\Console;

use PHPUnit\Framework\TestCase;
use LegalStudy\Console\Application;
use LegalStudy\Console\Commands\HealthCheckCommand;

class ApplicationTest extends TestCase
{
    private $application;

    protected function setUp(): void
    {
        parent::setUp();
        $this->application = new Application();
    }

    public function testShowHelp(): void
    {
        $result = $this->application->run(['console.php']);
        
        $this->assertEquals(0, $result);
        $output = $this->application->getOutput();
        $this->assertStringContainsString('Legal Study Console', implode("\n", $output));
        $this->assertStringContainsString('Available commands:', implode("\n", $output));
    }

    public function testRunCommand(): void
    {
        $this->application->register(new HealthCheckCommand());
        $result = $this->application->run(['console.php', 'health:check']);
        
        $this->assertEquals(0, $result);
        $output = $this->application->getOutput();
        $this->assertStringContainsString('System Health Status:', implode("\n", $output));
    }

    public function testRunCommandWithOptions(): void
    {
        $this->application->register(new HealthCheckCommand());
        $result = $this->application->run(['console.php', 'health:check', '--verbose']);
        
        $this->assertEquals(0, $result);
        $output = $this->application->getOutput();
        $this->assertStringContainsString('Detailed Health Check Results:', implode("\n", $output));
    }

    public function testRunNonExistentCommand(): void
    {
        $result = $this->application->run(['console.php', 'nonexistent:command']);
        
        $this->assertEquals(1, $result);
        $output = $this->application->getOutput();
        $this->assertStringContainsString("Command 'nonexistent:command' not found.", implode("\n", $output));
    }

    public function testParseInput(): void
    {
        $this->application->register(new HealthCheckCommand());
        $result = $this->application->run(['console.php', 'health:check', '--component', 'database', '--verbose']);
        
        $this->assertEquals(0, $result);
        $output = $this->application->getOutput();
        $this->assertStringContainsString('database: OK', implode("\n", $output));
        $this->assertStringContainsString('Detailed Health Check Results:', implode("\n", $output));
    }
} 