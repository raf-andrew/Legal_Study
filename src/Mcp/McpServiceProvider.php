<?php

namespace App\Mcp;

use Illuminate\Support\ServiceProvider as BaseServiceProvider;
use Illuminate\Support\Facades\Config;
use Mcp\Agent\AgentManager;
use Mcp\Agent\AgentLifecycleManager;
use Mcp\Agent\Communication\AgentCommunicationManager;
use Mcp\Configuration\ConfigurationManager;
use Mcp\Security\SecurityManager;
use Mcp\EventBus\EventBus;

class McpServiceProvider extends BaseServiceProvider
{
    public function register(): void
    {
        $this->app->singleton(AgentManager::class, function ($app) {
            return new AgentManager();
        });

        $this->app->singleton(AgentLifecycleManager::class, function ($app) {
            return new AgentLifecycleManager($app->make(AgentManager::class));
        });

        $this->app->singleton(AgentCommunicationManager::class, function ($app) {
            return new AgentCommunicationManager();
        });

        $this->app->singleton(ConfigurationManager::class, function ($app) {
            return new ConfigurationManager();
        });

        $this->app->singleton(SecurityManager::class, function ($app) {
            return new SecurityManager();
        });

        $this->app->singleton(EventBus::class, function ($app) {
            return new EventBus();
        });
    }

    public function boot(): void
    {
        $this->publishConfig();
        $this->loadMigrationsFrom(__DIR__.'/../database/migrations');
    }

    protected function publishConfig()
    {
        $this->publishes([
            __DIR__ . '/../config/mcp.php' => config_path('mcp.php'),
        ], 'mcp-config');
    }
} 