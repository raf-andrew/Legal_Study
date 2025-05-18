<?php

namespace Tests\Mcp\Console\Commands;

use Mcp\Console\Commands\McpGenerate;
use Mcp\Console\Generator\CodeGenerator;
use Tests\TestCase;
use Mockery;

class McpGenerateTest extends TestCase
{
    private McpGenerate $command;
    private CodeGenerator $generator;

    protected function setUp(): void
    {
        parent::setUp();
        
        $this->generator = Mockery::mock(CodeGenerator::class);
        $this->command = new McpGenerate($this->generator);
    }

    public function testGenerateCommand(): void
    {
        $this->generator->shouldReceive('generateClass')
            ->once()
            ->with(
                'command',
                'TestCommand',
                'App\\Console\\Commands',
                [
                    'command' => 'test_command',
                    'description' => 'The TestCommand command'
                ]
            )
            ->andReturn('/path/to/TestCommand.php');

        $this->artisan('mcp:generate', [
            'type' => 'command',
            'name' => 'TestCommand'
        ])
        ->expectsOutput('Generated command class at: /path/to/TestCommand.php')
        ->assertExitCode(0);
    }

    public function testGenerateCommandWithTest(): void
    {
        $this->generator->shouldReceive('generateClass')
            ->once()
            ->with(
                'command',
                'TestCommand',
                'App\\Console\\Commands',
                [
                    'command' => 'test_command',
                    'description' => 'The TestCommand command'
                ]
            )
            ->andReturn('/path/to/TestCommand.php');

        $this->generator->shouldReceive('generateTest')
            ->once()
            ->with(
                'command',
                'TestCommand',
                'App\\Console\\Commands',
                [
                    'command' => 'test_command',
                    'description' => 'The TestCommand command'
                ]
            )
            ->andReturn('/path/to/TestCommandTest.php');

        $this->artisan('mcp:generate', [
            'type' => 'command',
            'name' => 'TestCommand',
            '--test' => true
        ])
        ->expectsOutput('Generated command class at: /path/to/TestCommand.php')
        ->expectsOutput('Generated test class at: /path/to/TestCommandTest.php')
        ->assertExitCode(0);
    }

    public function testGenerateController(): void
    {
        $this->generator->shouldReceive('generateClass')
            ->once()
            ->with(
                'controller',
                'UserController',
                'App\\Http\\Controllers',
                [
                    'controller' => 'user',
                    'model' => 'User'
                ]
            )
            ->andReturn('/path/to/UserController.php');

        $this->artisan('mcp:generate', [
            'type' => 'controller',
            'name' => 'UserController'
        ])
        ->expectsOutput('Generated controller class at: /path/to/UserController.php')
        ->assertExitCode(0);
    }

    public function testGenerateModel(): void
    {
        $this->generator->shouldReceive('generateClass')
            ->once()
            ->with(
                'model',
                'User',
                'App\\Models',
                [
                    'table' => 'users',
                    'fillable' => '[]'
                ]
            )
            ->andReturn('/path/to/User.php');

        $this->artisan('mcp:generate', [
            'type' => 'model',
            'name' => 'User'
        ])
        ->expectsOutput('Generated model class at: /path/to/User.php')
        ->assertExitCode(0);
    }

    public function testGenerateWithCustomNamespace(): void
    {
        $this->generator->shouldReceive('generateClass')
            ->once()
            ->with(
                'controller',
                'UserController',
                'App\\Custom\\Namespace',
                [
                    'controller' => 'user',
                    'model' => 'User'
                ]
            )
            ->andReturn('/path/to/UserController.php');

        $this->artisan('mcp:generate', [
            'type' => 'controller',
            'name' => 'UserController',
            '--namespace' => 'App\\Custom\\Namespace'
        ])
        ->expectsOutput('Generated controller class at: /path/to/UserController.php')
        ->assertExitCode(0);
    }

    public function testGenerateWithNestedNamespace(): void
    {
        $this->generator->shouldReceive('generateClass')
            ->once()
            ->with(
                'controller',
                'UserController',
                'App\\Http\\Controllers\\Admin',
                [
                    'controller' => 'user',
                    'model' => 'User'
                ]
            )
            ->andReturn('/path/to/UserController.php');

        $this->artisan('mcp:generate', [
            'type' => 'controller',
            'name' => 'Admin/UserController'
        ])
        ->expectsOutput('Generated controller class at: /path/to/UserController.php')
        ->assertExitCode(0);
    }

    public function testGenerateWithError(): void
    {
        $this->generator->shouldReceive('generateClass')
            ->once()
            ->andThrow(new \RuntimeException('File already exists'));

        $this->artisan('mcp:generate', [
            'type' => 'controller',
            'name' => 'UserController'
        ])
        ->expectsOutput('File already exists')
        ->assertExitCode(1);
    }

    public function testGenerateService(): void
    {
        $this->generator->shouldReceive('generateClass')
            ->once()
            ->with(
                'service',
                'UserService',
                'App\\Services',
                [
                    'service' => 'user',
                    'dependencies' => ''
                ]
            )
            ->andReturn('/path/to/UserService.php');

        $this->artisan('mcp:generate', [
            'type' => 'service',
            'name' => 'UserService'
        ])
        ->expectsOutput('Generated service class at: /path/to/UserService.php')
        ->assertExitCode(0);
    }

    public function testGenerateEvent(): void
    {
        $this->generator->shouldReceive('generateClass')
            ->once()
            ->with(
                'event',
                'UserCreated',
                'App\\Events',
                [
                    'event' => 'user_created',
                    'properties' => ''
                ]
            )
            ->andReturn('/path/to/UserCreated.php');

        $this->artisan('mcp:generate', [
            'type' => 'event',
            'name' => 'UserCreated'
        ])
        ->expectsOutput('Generated event class at: /path/to/UserCreated.php')
        ->assertExitCode(0);
    }

    public function testGenerateListener(): void
    {
        $this->generator->shouldReceive('generateClass')
            ->once()
            ->with(
                'listener',
                'SendWelcomeEmailListener',
                'App\\Listeners',
                [
                    'listener' => 'send_welcome_email',
                    'event' => 'SendWelcomeEmail'
                ]
            )
            ->andReturn('/path/to/SendWelcomeEmailListener.php');

        $this->artisan('mcp:generate', [
            'type' => 'listener',
            'name' => 'SendWelcomeEmailListener'
        ])
        ->expectsOutput('Generated listener class at: /path/to/SendWelcomeEmailListener.php')
        ->assertExitCode(0);
    }

    public function testGeneratePolicy(): void
    {
        $this->generator->shouldReceive('generateClass')
            ->once()
            ->with(
                'policy',
                'UserPolicy',
                'App\\Policies',
                [
                    'policy' => 'user',
                    'model' => 'User'
                ]
            )
            ->andReturn('/path/to/UserPolicy.php');

        $this->artisan('mcp:generate', [
            'type' => 'policy',
            'name' => 'UserPolicy'
        ])
        ->expectsOutput('Generated policy class at: /path/to/UserPolicy.php')
        ->assertExitCode(0);
    }
} 