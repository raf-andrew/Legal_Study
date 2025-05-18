<?php

namespace LegalStudy\ModularInitialization;

use Illuminate\Support\ServiceProvider;
use LegalStudy\ModularInitialization\Services\InitializationStateManager;
use LegalStudy\ModularInitialization\Services\InitializationStatus;
use LegalStudy\ModularInitialization\Contracts\InitializationInterface;

class ModularInitializationServiceProvider extends ServiceProvider
{
    public function register()
    {
        $this->app->singleton(InitializationStateManager::class, function ($app) {
            return new InitializationStateManager(new InitializationStatus());
        });

        $this->app->bind(InitializationInterface::class, InitializationStateManager::class);
    }

    public function boot()
    {
        $this->publishes([
            __DIR__ . '/../config/modular-initialization.php' => config_path('modular-initialization.php'),
        ], 'config');

        $this->mergeConfigFrom(
            __DIR__ . '/../config/modular-initialization.php', 'modular-initialization'
        );
    }
} 