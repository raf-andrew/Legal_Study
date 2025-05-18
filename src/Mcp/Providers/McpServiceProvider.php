<?php

namespace Mcp\Providers;

use Illuminate\Support\ServiceProvider;
use Mcp\Discovery\Discovery;
use Mcp\Discovery\ServiceRegistry;
use Mcp\Discovery\ServiceHealthMonitor;

class McpServiceProvider extends ServiceProvider
{
    /**
     * Register services.
     *
     * @return void
     */
    public function register(): void
    {
        // Register MCP configuration
        $this->mergeConfigFrom(
            __DIR__.'/../../config/mcp.php', 'mcp'
        );

        // Register MCP services
        $this->app->singleton(Discovery::class, function ($app) {
            return new Discovery();
        });

        $this->app->singleton(ServiceRegistry::class, function ($app) {
            return new ServiceRegistry();
        });

        $this->app->singleton(ServiceHealthMonitor::class, function ($app) {
            return new ServiceHealthMonitor();
        });

        // Register MCP commands
        $this->commands([
            \Mcp\Console\Commands\McpDiscover::class,
            \Mcp\Console\Commands\McpMonitor::class,
            \Mcp\Console\Commands\McpStatus::class,
        ]);
    }

    /**
     * Bootstrap services.
     *
     * @return void
     */
    public function boot(): void
    {
        // Publish MCP configuration
        $this->publishes([
            __DIR__.'/../../config/mcp.php' => config_path('mcp.php'),
        ], 'mcp-config');

        // Publish MCP assets
        $this->publishes([
            __DIR__.'/../../resources/assets' => public_path('vendor/mcp'),
        ], 'mcp-assets');

        // Load MCP routes
        $this->loadRoutesFrom(__DIR__.'/../../routes/mcp.php');

        // Load MCP views
        $this->loadViewsFrom(__DIR__.'/../../resources/views', 'mcp');

        // Load MCP translations
        $this->loadTranslationsFrom(__DIR__.'/../../resources/lang', 'mcp');

        // Register MCP middleware
        $this->app['router']->aliasMiddleware('mcp', \Mcp\Http\Middleware\McpMiddleware::class);

        // Register MCP event listeners
        $this->registerEventListeners();
    }

    /**
     * Register event listeners.
     *
     * @return void
     */
    protected function registerEventListeners(): void
    {
        // Listen for service discovery events
        $this->app['events']->listen(
            \Mcp\Events\ServiceDiscovered::class,
            \Mcp\Listeners\ServiceDiscoveredListener::class
        );

        // Listen for service health events
        $this->app['events']->listen(
            \Mcp\Events\ServiceHealthChanged::class,
            \Mcp\Listeners\ServiceHealthChangedListener::class
        );

        // Listen for service error events
        $this->app['events']->listen(
            \Mcp\Events\ServiceError::class,
            \Mcp\Listeners\ServiceErrorListener::class
        );
    }

    /**
     * Get the services provided by the provider.
     *
     * @return array
     */
    public function provides(): array
    {
        return [
            Discovery::class,
            ServiceRegistry::class,
            ServiceHealthMonitor::class,
        ];
    }
} 