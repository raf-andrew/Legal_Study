<?php

namespace App\Providers;

use Illuminate\Support\ServiceProvider;
use App\Services\CodespacesServiceManager;
use App\Services\CodespacesHealthCheck;
use App\Services\CodespacesLifecycleManager;
use App\Services\CodespacesHealthCheckService;

class CodespacesServiceProvider extends ServiceProvider
{
    /**
     * Register services.
     */
    public function register(): void
    {
        $this->app->singleton(CodespacesServiceManager::class, function ($app) {
            return new CodespacesServiceManager();
        });

        $this->app->singleton(CodespacesHealthCheck::class, function ($app) {
            return new CodespacesHealthCheck();
        });

        $this->app->singleton(CodespacesLifecycleManager::class, function ($app) {
            return new CodespacesLifecycleManager();
        });

        $this->app->singleton(CodespacesHealthCheckService::class, function ($app) {
            return new CodespacesHealthCheckService();
        });
    }

    /**
     * Bootstrap services.
     */
    public function boot(): void
    {
        // Load Codespaces configuration
        $this->mergeConfigFrom(
            __DIR__.'/../../config/codespaces.php', 'codespaces'
        );

        // Publish configuration
        $this->publishes([
            __DIR__.'/../../config/codespaces.php' => config_path('codespaces.php'),
        ], 'codespaces-config');
    }
}
