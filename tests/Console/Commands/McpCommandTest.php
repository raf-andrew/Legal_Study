<?php

namespace Tests\Console\Commands;

use App\Console\Commands\McpCommand;
use App\Mcp\Core\Server;
use Illuminate\Support\Facades\Config;
use Tests\TestCase;

class McpCommandTest extends TestCase
{
    protected McpCommand $command;
    protected Server $server;

    protected function setUp(): void
    {
        parent::setUp();
        $this->server = new Server();
        $this->command = new McpCommand($this->server);
    }

    public function test_command_initialization(): void
    {
        $this->assertInstanceOf(McpCommand::class, $this->command);
    }

    public function test_status_option(): void
    {
        Config::set('app.env', 'local');
        Config::set('mcp.enabled', true);

        $this->artisan('mcp --status')
            ->expectsOutput('MCP Server Status:')
            ->expectsOutput('Environment: Development')
            ->expectsOutput('Enabled: Yes')
            ->assertExitCode(0);
    }

    public function test_metrics_option(): void
    {
        Config::set('app.env', 'local');
        Config::set('mcp.enabled', true);

        $this->artisan('mcp --metrics')
            ->expectsOutput('MCP Server Metrics:')
            ->expectsOutputMatches('/Timestamp: .*/')
            ->expectsOutputMatches('/CPU Usage: .*/')
            ->expectsOutput('Memory Usage:')
            ->expectsOutputMatches('/  Total: .*/')
            ->expectsOutputMatches('/  Peak: .*/')
            ->expectsOutput('Disk Usage:')
            ->expectsOutputMatches('/  Total: .*/')
            ->expectsOutputMatches('/  Free: .*/')
            ->expectsOutputMatches('/  Used: .*/')
            ->expectsOutputMatches('/  Usage: .*/')
            ->assertExitCode(0);
    }

    public function test_services_option(): void
    {
        Config::set('app.env', 'local');
        Config::set('mcp.enabled', true);

        $this->artisan('mcp --services')
            ->expectsOutput('Registered Services:')
            ->expectsOutput('No services registered.')
            ->assertExitCode(0);
    }

    public function test_start_action(): void
    {
        Config::set('app.env', 'local');
        Config::set('mcp.enabled', true);

        $this->artisan('mcp start')
            ->expectsOutput('Starting MCP server...')
            ->expectsOutput('MCP server started successfully.')
            ->assertExitCode(0);
    }

    public function test_stop_action(): void
    {
        Config::set('app.env', 'local');
        Config::set('mcp.enabled', true);

        $this->artisan('mcp stop')
            ->expectsOutput('Stopping MCP server...')
            ->expectsOutput('MCP server stopped successfully.')
            ->assertExitCode(0);
    }

    public function test_restart_action(): void
    {
        Config::set('app.env', 'local');
        Config::set('mcp.enabled', true);

        $this->artisan('mcp restart')
            ->expectsOutput('Restarting MCP server...')
            ->expectsOutput('MCP server restarted successfully.')
            ->assertExitCode(0);
    }

    public function test_unknown_action(): void
    {
        Config::set('app.env', 'local');
        Config::set('mcp.enabled', true);

        $this->artisan('mcp unknown')
            ->expectsOutput('Unknown action: unknown')
            ->expectsOutput('Usage:')
            ->assertExitCode(1);
    }

    public function test_disabled_server(): void
    {
        Config::set('app.env', 'production');
        Config::set('mcp.enabled', false);

        $this->artisan('mcp status')
            ->expectsOutput('MCP server is disabled. Enable it in the configuration to use this command.')
            ->assertExitCode(1);
    }

    public function test_help_display(): void
    {
        Config::set('app.env', 'local');
        Config::set('mcp.enabled', true);

        $this->artisan('mcp')
            ->expectsOutput('Usage:')
            ->expectsOutput('  php artisan mcp <action> [options]')
            ->expectsOutput('Actions:')
            ->expectsOutput('  start     Start the MCP server')
            ->expectsOutput('  stop      Stop the MCP server')
            ->expectsOutput('  restart   Restart the MCP server')
            ->expectsOutput('Options:')
            ->expectsOutput('  --status    Show server status')
            ->expectsOutput('  --metrics   Show server metrics')
            ->expectsOutput('  --services  Show registered services')
            ->assertExitCode(0);
    }
} 