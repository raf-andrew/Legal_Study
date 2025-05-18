<?php

namespace Tests\Mcp\Console\Commands;

use Mcp\Console\Commands\McpActuate;
use Mcp\Service\ServiceActuator;
use Tests\TestCase;
use Mockery;

class McpActuateTest extends TestCase
{
    private $actuator;
    private $command;
    private $mockServiceClass = 'Tests\\Mcp\\Console\\Commands\\MockService';

    protected function setUp(): void
    {
        parent::setUp();
        $this->actuator = Mockery::mock(ServiceActuator::class);
        $this->command = new McpActuate($this->actuator);
        app()->bind($this->mockServiceClass, function () {
            return new MockService();
        });
    }

    public function testInvokeSuccess()
    {
        $this->actuator->shouldReceive('invoke')
            ->once()
            ->with(Mockery::type(MockService::class), 'add', [1, 2])
            ->andReturn(3);

        $this->artisan('mcp:actuate', [
            'service' => $this->mockServiceClass,
            'method' => 'add',
            'params' => ['1', '2']
        ])
        ->expectsOutput('Invocation result:')
        ->expectsOutput('3')
        ->assertExitCode(0);
    }

    public function testServiceClassNotFound()
    {
        $this->artisan('mcp:actuate', [
            'service' => 'NonExistentClass',
            'method' => 'add',
            'params' => ['1', '2']
        ])
        ->expectsOutput('Service class NonExistentClass does not exist.')
        ->assertExitCode(1);
    }

    public function testMethodNotFound()
    {
        $this->actuator->shouldReceive('invoke')
            ->once()
            ->andThrow(new \BadMethodCallException('Method not found'));

        $this->artisan('mcp:actuate', [
            'service' => $this->mockServiceClass,
            'method' => 'nonExistent',
            'params' => []
        ])
        ->expectsOutput('Invocation failed: Method not found')
        ->assertExitCode(1);
    }

    public function testInvalidParams()
    {
        $this->actuator->shouldReceive('invoke')
            ->once()
            ->andThrow(new \InvalidArgumentException('Not enough parameters'));

        $this->artisan('mcp:actuate', [
            'service' => $this->mockServiceClass,
            'method' => 'add',
            'params' => ['1']
        ])
        ->expectsOutput('Invocation failed: Not enough parameters')
        ->assertExitCode(1);
    }

    public function testExceptionThrownByService()
    {
        $this->actuator->shouldReceive('invoke')
            ->once()
            ->andThrow(new \RuntimeException('Service error'));

        $this->artisan('mcp:actuate', [
            'service' => $this->mockServiceClass,
            'method' => 'throws',
            'params' => []
        ])
        ->expectsOutput('Invocation failed: Service error')
        ->assertExitCode(1);
    }

    public function testJsonOutput()
    {
        $this->actuator->shouldReceive('invoke')
            ->once()
            ->andReturn(['result' => 42]);

        $this->artisan('mcp:actuate', [
            'service' => $this->mockServiceClass,
            'method' => 'add',
            'params' => ['21', '21'],
            '--json' => true
        ])
        ->expectsOutput(json_encode(['result' => ['result' => 42]], JSON_PRETTY_PRINT))
        ->assertExitCode(0);
    }
}

class MockService
{
    public function add($a, $b) { return $a + $b; }
    public function throws() { throw new \RuntimeException('Service error'); }
} 