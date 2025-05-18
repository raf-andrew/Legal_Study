<?php

namespace LegalStudy\Console\Tests;

use LegalStudy\Console\Application;
use LegalStudy\Console\Commands\HealthCheckCommand;
use PHPUnit\Framework\TestCase;

class ApplicationTest extends TestCase
{
    private Application $app;
    private HealthCheckCommand $healthCheckCommand;

    protected function setUp(): void
    {
        $this->app = new Application();
        $this->healthCheckCommand = new HealthCheckCommand();
        $this->app->registerCommand($this->healthCheckCommand);
    }

    public function testRunWithNoArguments()
    {
        $result = $this->app->run(['console.php']);
        $this->assertEquals(1, $result);
    }

    public function testRunWithHelpCommand()
    {
        $result = $this->app->run(['console.php', 'help']);
        $this->assertEquals(0, $result);
    }

    public function testRunWithSpecificCommandHelp()
    {
        $result = $this->app->run(['console.php', 'help', 'health:check']);
        $this->assertEquals(0, $result);
    }

    public function testRunWithHealthCheckCommand()
    {
        $result = $this->app->run(['console.php', 'health:check']);
        $this->assertEquals(0, $result);
    }

    public function testRunWithHealthCheckCommandAndArguments()
    {
        $result = $this->app->run(['console.php', 'health:check', '--component=database', '--verbose']);
        $this->assertEquals(0, $result);
    }

    public function testRunWithNonExistentCommand()
    {
        $result = $this->app->run(['console.php', 'nonexistent']);
        $this->assertEquals(1, $result);
    }

    public function testParseArguments()
    {
        $reflection = new \ReflectionClass(Application::class);
        $method = $reflection->getMethod('parseArguments');
        $method->setAccessible(true);

        $app = new Application();
        $result = $method->invoke($app, ['--option1', 'value1', '--option2', '--option3', 'value3']);

        $this->assertEquals([
            'option1' => 'value1',
            'option2' => true,
            'option3' => 'value3'
        ], $result);
    }

    public function testParseArgumentsWithPositionalArgs()
    {
        $reflection = new \ReflectionClass(Application::class);
        $method = $reflection->getMethod('parseArguments');
        $method->setAccessible(true);

        $app = new Application();
        $result = $method->invoke($app, ['arg1', '--option1', 'value1', 'arg2']);

        $this->assertEquals([
            0 => 'arg1',
            'option1' => 'value1',
            1 => 'arg2'
        ], $result);
    }
} 