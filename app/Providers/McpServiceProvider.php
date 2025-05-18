<?php

namespace App\Providers;

use App\Mcp\Core\Server;
use Illuminate\Support\ServiceProvider;

class McpServiceProvider extends ServiceProvider
{
    /**
     * Register services.
     */
    public function register(): void
    {
        $this->app->singleton(Server::class, function ($app) {
            return new Server();
        });
    }

    /**
     * Bootstrap services.
     */
    public function boot(): void
    {
        $this->publishes([
            __DIR__.'/../../config/mcp.php' => config_path('mcp.php'),
        ], 'mcp-config');
    }
} 