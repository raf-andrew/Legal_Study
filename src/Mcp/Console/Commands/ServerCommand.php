<?php

namespace App\Mcp\Console\Commands;

use App\Mcp\Server;
use App\Mcp\ConfigurationManager;
use Symfony\Component\Console\Input\InputArgument;
use Symfony\Component\Console\Input\InputOption;

class ServerCommand extends McpCommand
{
    protected $signature = 'mcp:server
                          {action : Action to perform (status|config|features|services)}
                          {--format=table : Output format (table|json)}';

    protected $description = 'Manage MCP server';

    protected $configManager;

    public function __construct(Server $server)
    {
        parent::__construct($server);
        $this->configManager = $server->getService(ConfigurationManager::class);
    }

    public function handle()
    {
        $action = $this->argument('action');
        
        try {
            switch ($action) {
                case 'status':
                    return $this->showStatus();
                case 'config':
                    return $this->showConfig();
                case 'features':
                    return $this->showFeatures();
                case 'services':
                    return $this->showServices();
                default:
                    $this->error("Unknown action: {$action}");
                    return 1;
            }
        } catch (\Exception $e) {
            return $this->handleException($e);
        }
    }

    protected function showStatus()
    {
        $data = [
            'enabled' => $this->server->isEnabled() ? 'Yes' : 'No',
            'development_mode' => $this->server->isDevelopment() ? 'Yes' : 'No',
            'registered_services' => count($this->server->getServices()),
            'event_bus_status' => $this->server->getEventBus() ? 'Active' : 'Inactive',
        ];

        $this->line($this->formatOutput($data, $this->option('format')));
        return 0;
    }

    protected function showConfig()
    {
        $config = $this->configManager->get();
        
        // Flatten config for table display
        $data = [];
        $this->flattenConfig($config, $data);

        $this->line($this->formatOutput($data, $this->option('format')));
        return 0;
    }

    protected function showFeatures()
    {
        $features = $this->configManager->get('features');
        
        $data = array_map(function ($feature, $enabled) {
            return [
                'feature' => $feature,
                'enabled' => $enabled ? 'Yes' : 'No',
            ];
        }, array_keys($features), $features);

        $this->line($this->formatOutput($data, $this->option('format')));
        return 0;
    }

    protected function showServices()
    {
        $services = $this->server->getServices();
        
        $data = array_map(function ($service) {
            return [
                'service' => get_class($service),
                'status' => 'Active',
            ];
        }, $services);

        $this->line($this->formatOutput($data, $this->option('format')));
        return 0;
    }

    protected function flattenConfig(array $config, array &$result, string $prefix = '')
    {
        foreach ($config as $key => $value) {
            $fullKey = $prefix ? "{$prefix}.{$key}" : $key;
            
            if (is_array($value) && !$this->isAssociative($value)) {
                $result[$fullKey] = implode(', ', $value);
            } elseif (is_array($value)) {
                $this->flattenConfig($value, $result, $fullKey);
            } else {
                $result[$fullKey] = is_bool($value) ? ($value ? 'Yes' : 'No') : $value;
            }
        }
    }

    protected function isAssociative(array $array)
    {
        if (empty($array)) {
            return false;
        }
        return array_keys($array) !== range(0, count($array) - 1);
    }
} 