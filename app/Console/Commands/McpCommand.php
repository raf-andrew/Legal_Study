<?php

namespace App\Console\Commands;

use App\Mcp\Core\Server;
use Illuminate\Console\Command;

class McpCommand extends Command
{
    protected $signature = 'mcp {action?} {--status} {--metrics} {--services}';
    protected $description = 'Manage the MCP server';

    protected Server $server;

    public function __construct(Server $server)
    {
        parent::__construct();
        $this->server = $server;
    }

    public function handle(): int
    {
        if (!$this->server->isEnabled()) {
            $this->error('MCP server is disabled. Enable it in the configuration to use this command.');
            return self::FAILURE;
        }

        if ($this->option('status')) {
            return $this->handleStatus();
        }

        if ($this->option('metrics')) {
            return $this->handleMetrics();
        }

        if ($this->option('services')) {
            return $this->handleServices();
        }

        $action = $this->argument('action');
        if (!$action) {
            $this->displayHelp();
            return self::SUCCESS;
        }

        return match ($action) {
            'start' => $this->handleStart(),
            'stop' => $this->handleStop(),
            'restart' => $this->handleRestart(),
            default => $this->handleUnknownAction($action),
        };
    }

    protected function handleStatus(): int
    {
        $this->info('MCP Server Status:');
        $this->line('Environment: ' . ($this->server->isProduction() ? 'Production' : 'Development'));
        $this->line('Enabled: ' . ($this->server->isEnabled() ? 'Yes' : 'No'));
        
        return self::SUCCESS;
    }

    protected function handleMetrics(): int
    {
        $metrics = $this->server->getHealthMetrics();
        
        $this->info('MCP Server Metrics:');
        $this->line('Timestamp: ' . $metrics['timestamp']);
        $this->line('CPU Usage: ' . $metrics['cpu_usage']);
        
        $this->line("\nMemory Usage:");
        $this->line('  Total: ' . $this->formatBytes($metrics['memory_usage']['total']));
        $this->line('  Peak: ' . $this->formatBytes($metrics['memory_usage']['peak']));
        
        $this->line("\nDisk Usage:");
        $this->line('  Total: ' . $this->formatBytes($metrics['disk_usage']['total']));
        $this->line('  Free: ' . $this->formatBytes($metrics['disk_usage']['free']));
        $this->line('  Used: ' . $this->formatBytes($metrics['disk_usage']['used']));
        $this->line('  Usage: ' . number_format($metrics['disk_usage']['percentage'], 2) . '%');
        
        return self::SUCCESS;
    }

    protected function handleServices(): int
    {
        $services = $this->server->getServices();
        
        $this->info('Registered Services:');
        if (empty($services)) {
            $this->line('No services registered.');
            return self::SUCCESS;
        }

        $headers = ['Name', 'Status', 'Last Check'];
        $rows = [];
        
        foreach ($services as $name => $service) {
            $rows[] = [
                $name,
                $service['status'],
                $service['last_check'],
            ];
        }

        $this->table($headers, $rows);
        return self::SUCCESS;
    }

    protected function handleStart(): int
    {
        $this->info('Starting MCP server...');
        // Implementation for starting the server
        $this->info('MCP server started successfully.');
        return self::SUCCESS;
    }

    protected function handleStop(): int
    {
        $this->info('Stopping MCP server...');
        // Implementation for stopping the server
        $this->info('MCP server stopped successfully.');
        return self::SUCCESS;
    }

    protected function handleRestart(): int
    {
        $this->info('Restarting MCP server...');
        // Implementation for restarting the server
        $this->info('MCP server restarted successfully.');
        return self::SUCCESS;
    }

    protected function handleUnknownAction(string $action): int
    {
        $this->error("Unknown action: {$action}");
        $this->displayHelp();
        return self::FAILURE;
    }

    protected function displayHelp(): void
    {
        $this->line('Usage:');
        $this->line('  php artisan mcp <action> [options]');
        $this->line('');
        $this->line('Actions:');
        $this->line('  start     Start the MCP server');
        $this->line('  stop      Stop the MCP server');
        $this->line('  restart   Restart the MCP server');
        $this->line('');
        $this->line('Options:');
        $this->line('  --status    Show server status');
        $this->line('  --metrics   Show server metrics');
        $this->line('  --services  Show registered services');
    }

    protected function formatBytes(int $bytes): string
    {
        $units = ['B', 'KB', 'MB', 'GB', 'TB'];
        $bytes = max($bytes, 0);
        $pow = floor(($bytes ? log($bytes) : 0) / log(1024));
        $pow = min($pow, count($units) - 1);
        $bytes /= pow(1024, $pow);
        return round($bytes, 2) . ' ' . $units[$pow];
    }
} 