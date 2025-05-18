<?php

namespace App\Providers;

use App\Services\Discovery;
use App\Events\EventBus;
use App\Config\ConfigurationManager;
use Mcp\Console\Commands\McpConfig;
use Illuminate\Support\ServiceProvider;

class McpServiceProvider extends ServiceProvider
{
    public function register(): void
    {
        $this->app->singleton(Discovery::class, function ($app) {
            return new Discovery(
                $app->make('config')->get('mcp.services_path')
            );
        });

        $this->app->singleton(EventBus::class, function ($app) {
            return new EventBus(
                $app->make('cache.store'),
                $app->make('config')->get('mcp.max_event_history', 1000)
            );
        });

        $this->app->singleton(ConfigurationManager::class, function ($app) {
            $manager = new ConfigurationManager($app->environment());
            
            // Load default configuration if available
            $configPath = $app->make('config')->get('mcp.config_path');
            if ($configPath && file_exists($configPath)) {
                $manager->load($configPath);
            }
            
            return $manager;
        });

        // Register config
        $this->mergeConfigFrom(
            __DIR__.'/../../config/mcp.php',
            'mcp'
        );
    }

    public function boot(): void
    {
        // Publish configuration
        $this->publishes([
            __DIR__.'/../../config/mcp.php' => config_path('mcp.php'),
        ], 'mcp-config');

        // Register console commands if running in console
        if ($this->app->runningInConsole()) {
            $this->commands([
                McpConfig::class
            ]);
        }

        // Initialize service discovery
        $discovery = $this->app->make(Discovery::class);
        $discovery->discoverServices();

        // Register event listeners
        $eventBus = $this->app->make(EventBus::class);
        $this->registerEventListeners($eventBus);
    }

    private function registerEventListeners(EventBus $eventBus): void
    {
        // Register system events
        $eventBus->subscribe('mcp.service.discovered', function ($event) {
            logger()->info('Service discovered', $event['payload']);
        });

        $eventBus->subscribe('mcp.config.changed', function ($event) {
            logger()->info('Configuration changed', $event['payload']);
        });

        // Register error events
        $eventBus->subscribe('mcp.error', function ($event) {
            logger()->error('MCP Error', $event['payload']);
        });
    }
} 