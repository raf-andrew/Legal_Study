<?php

namespace Mcp\Console\Commands;

use Illuminate\Console\Command;
use Mcp\ConfigurationManager;
use Symfony\Component\Console\Helper\Table;

class McpConfig extends Command
{
    protected $signature = 'mcp:config
                          {action : The action to perform (get|set|list|enable|disable|validate)}
                          {key? : The configuration key}
                          {value? : The value to set}
                          {--env= : The environment to target}';

    protected $description = 'Manage MCP configuration';

    protected ConfigurationManager $manager;

    public function __construct(ConfigurationManager $manager)
    {
        parent::__construct();
        $this->manager = $manager;
    }

    public function handle(): int
    {
        $action = $this->argument('action');
        $key = $this->argument('key');
        $value = $this->argument('value');

        try {
            switch ($action) {
                case 'get':
                    if (!$key) {
                        $this->error('Key is required for get action');
                        return 1;
                    }
                    $this->showValue($key);
                    break;

                case 'set':
                    if (!$key || !$value) {
                        $this->error('Key and value are required for set action');
                        return 1;
                    }
                    $this->setValue($key, $value);
                    break;

                case 'list':
                    $this->listConfiguration();
                    break;

                case 'enable':
                    if (!$key) {
                        $this->error('Feature name is required for enable action');
                        return 1;
                    }
                    $this->enableFeature($key);
                    break;

                case 'disable':
                    if (!$key) {
                        $this->error('Feature name is required for disable action');
                        return 1;
                    }
                    $this->disableFeature($key);
                    break;

                case 'validate':
                    $this->validateConfiguration();
                    break;

                default:
                    $this->error("Unknown action: {$action}");
                    return 1;
            }

            return 0;
        } catch (\Exception $e) {
            $this->error($e->getMessage());
            return 1;
        }
    }

    protected function showValue(string $key): void
    {
        $value = $this->manager->get($key);
        
        if (is_array($value)) {
            $this->info("\nConfiguration for {$key}:");
            $this->table(
                ['Key', 'Value'],
                collect($value)->map(function ($v, $k) {
                    return [$k, is_array($v) ? json_encode($v) : (string)$v];
                })
            );
        } else {
            $this->info("\nValue for {$key}: " . (is_bool($value) ? ($value ? 'true' : 'false') : $value));
        }
    }

    protected function setValue(string $key, string $value): void
    {
        // Convert string value to appropriate type
        $value = match (strtolower($value)) {
            'true' => true,
            'false' => false,
            'null' => null,
            default => is_numeric($value) ? (int)$value : $value
        };

        $this->manager->set($key, $value);
        $this->info("Configuration updated: {$key} = " . (is_bool($value) ? ($value ? 'true' : 'false') : $value));
    }

    protected function listConfiguration(): void
    {
        $config = $this->manager->get();
        
        $this->info("\nMCP Configuration:");
        $this->table(
            ['Key', 'Value'],
            $this->flattenConfig($config)
        );
    }

    protected function enableFeature(string $feature): void
    {
        $this->manager->set("features.{$feature}", true);
        $this->info("Feature enabled: {$feature}");
    }

    protected function disableFeature(string $feature): void
    {
        $this->manager->set("features.{$feature}", false);
        $this->info("Feature disabled: {$feature}");
    }

    protected function validateConfiguration(): void
    {
        $errors = $this->manager->validateConfiguration();
        
        if (empty($errors)) {
            $this->info('Configuration is valid');
            return;
        }

        $this->error('Configuration validation failed:');
        foreach ($errors as $error) {
            $this->line("  - {$error}");
        }
    }

    protected function flattenConfig(array $config, string $prefix = ''): array
    {
        $rows = [];
        
        foreach ($config as $key => $value) {
            $fullKey = $prefix ? "{$prefix}.{$key}" : $key;
            
            if (is_array($value)) {
                $rows = array_merge($rows, $this->flattenConfig($value, $fullKey));
            } else {
                $rows[] = [
                    $fullKey,
                    is_bool($value) ? ($value ? 'true' : 'false') : (string)$value
                ];
            }
        }
        
        return $rows;
    }
} 