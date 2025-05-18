<?php

namespace Tests\Mcp\Console\Commands;

use Mcp\Console\Commands\McpConfig;
use Mcp\ConfigurationManager;
use Tests\TestCase;
use Mockery;

class McpConfigTest extends TestCase
{
    private McpConfig $command;
    private ConfigurationManager $manager;

    protected function setUp(): void
    {
        parent::setUp();
        
        $this->manager = Mockery::mock(ConfigurationManager::class);
        $this->command = new McpConfig($this->manager);
    }

    public function testGetConfiguration(): void
    {
        $this->manager->shouldReceive('get')
            ->once()
            ->with('test.key')
            ->andReturn('test_value');

        $this->artisan('mcp:config', [
            'action' => 'get',
            'key' => 'test.key'
        ])
        ->expectsOutput("\nValue for test.key: test_value")
        ->assertExitCode(0);
    }

    public function testGetArrayConfiguration(): void
    {
        $this->manager->shouldReceive('get')
            ->once()
            ->with('test')
            ->andReturn([
                'key1' => 'value1',
                'key2' => 'value2'
            ]);

        $this->artisan('mcp:config', [
            'action' => 'get',
            'key' => 'test'
        ])
        ->expectsOutput("\nConfiguration for test:")
        ->assertExitCode(0);
    }

    public function testGetWithoutKey(): void
    {
        $this->artisan('mcp:config', ['action' => 'get'])
            ->expectsOutput('Key is required for get action')
            ->assertExitCode(1);
    }

    public function testSetConfiguration(): void
    {
        $this->manager->shouldReceive('set')
            ->once()
            ->with('test.key', 'test_value');

        $this->artisan('mcp:config', [
            'action' => 'set',
            'key' => 'test.key',
            'value' => 'test_value'
        ])
        ->expectsOutput('Configuration updated: test.key = test_value')
        ->assertExitCode(0);
    }

    public function testSetBooleanConfiguration(): void
    {
        $this->manager->shouldReceive('set')
            ->once()
            ->with('test.key', true);

        $this->artisan('mcp:config', [
            'action' => 'set',
            'key' => 'test.key',
            'value' => 'true'
        ])
        ->expectsOutput('Configuration updated: test.key = true')
        ->assertExitCode(0);
    }

    public function testSetNumericConfiguration(): void
    {
        $this->manager->shouldReceive('set')
            ->once()
            ->with('test.key', 123);

        $this->artisan('mcp:config', [
            'action' => 'set',
            'key' => 'test.key',
            'value' => '123'
        ])
        ->expectsOutput('Configuration updated: test.key = 123')
        ->assertExitCode(0);
    }

    public function testSetWithoutKeyValue(): void
    {
        $this->artisan('mcp:config', [
            'action' => 'set',
            'key' => 'test.key'
        ])
        ->expectsOutput('Key and value are required for set action')
        ->assertExitCode(1);
    }

    public function testListConfiguration(): void
    {
        $this->manager->shouldReceive('get')
            ->once()
            ->withNoArgs()
            ->andReturn([
                'key1' => 'value1',
                'nested' => [
                    'key2' => 'value2'
                ]
            ]);

        $this->artisan('mcp:config', ['action' => 'list'])
            ->expectsOutput("\nMCP Configuration:")
            ->assertExitCode(0);
    }

    public function testEnableFeature(): void
    {
        $this->manager->shouldReceive('set')
            ->once()
            ->with('features.test_feature', true);

        $this->artisan('mcp:config', [
            'action' => 'enable',
            'key' => 'test_feature'
        ])
        ->expectsOutput('Feature enabled: test_feature')
        ->assertExitCode(0);
    }

    public function testEnableWithoutFeature(): void
    {
        $this->artisan('mcp:config', ['action' => 'enable'])
            ->expectsOutput('Feature name is required for enable action')
            ->assertExitCode(1);
    }

    public function testDisableFeature(): void
    {
        $this->manager->shouldReceive('set')
            ->once()
            ->with('features.test_feature', false);

        $this->artisan('mcp:config', [
            'action' => 'disable',
            'key' => 'test_feature'
        ])
        ->expectsOutput('Feature disabled: test_feature')
        ->assertExitCode(0);
    }

    public function testDisableWithoutFeature(): void
    {
        $this->artisan('mcp:config', ['action' => 'disable'])
            ->expectsOutput('Feature name is required for disable action')
            ->assertExitCode(1);
    }

    public function testValidateConfiguration(): void
    {
        $this->manager->shouldReceive('validateConfiguration')
            ->once()
            ->andReturn([]);

        $this->artisan('mcp:config', ['action' => 'validate'])
            ->expectsOutput('Configuration is valid')
            ->assertExitCode(0);
    }

    public function testValidateConfigurationWithErrors(): void
    {
        $this->manager->shouldReceive('validateConfiguration')
            ->once()
            ->andReturn(['Error 1', 'Error 2']);

        $this->artisan('mcp:config', ['action' => 'validate'])
            ->expectsOutput('Configuration validation failed:')
            ->expectsOutput('  - Error 1')
            ->expectsOutput('  - Error 2')
            ->assertExitCode(0);
    }

    public function testUnknownAction(): void
    {
        $this->artisan('mcp:config', ['action' => 'unknown'])
            ->expectsOutput('Unknown action: unknown')
            ->assertExitCode(1);
    }

    public function testHandleException(): void
    {
        $this->manager->shouldReceive('get')
            ->once()
            ->andThrow(new \Exception('Test error'));

        $this->artisan('mcp:config', [
            'action' => 'get',
            'key' => 'test.key'
        ])
        ->expectsOutput('Test error')
        ->assertExitCode(1);
    }
} 