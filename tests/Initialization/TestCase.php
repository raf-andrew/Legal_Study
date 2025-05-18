<?php

namespace LegalStudy\ModularInitialization\Tests\Initialization;

use PHPUnit\Framework\TestCase as BaseTestCase;
use LegalStudy\ModularInitialization\ModularInitializationServiceProvider;

abstract class TestCase extends BaseTestCase
{
    protected function setUp(): void
    {
        parent::setUp();
        
        // Register our service provider
        $this->app->register(ModularInitializationServiceProvider::class);

        // Set up error and failure logging
        if (!is_dir('.errors')) {
            mkdir('.errors', 0755, true);
        }
        if (!is_dir('.failure')) {
            mkdir('.failure', 0755, true);
        }
    }

    protected function getPackageProviders($app)
    {
        return [
            ModularInitializationServiceProvider::class,
        ];
    }

    protected function getEnvironmentSetUp($app)
    {
        // Set up any environment variables needed for testing
        $app['config']->set('modular-initialization', [
            'permissions' => 0755,
            'required_dirs' => [
                'cache',
                'logs',
                'uploads',
            ],
            'initialization_order' => [
                'filesystem',
                'cache',
                'database',
                'queue',
            ],
            'error_handling' => [
                'throw_exceptions' => true,
                'log_errors' => true,
            ],
            'performance_monitoring' => [
                'enabled' => true,
                'threshold_ms' => 1000,
            ],
        ]);
    }

    /**
     * Creates the application.
     *
     * @return \Illuminate\Foundation\Application
     */
    public function createApplication()
    {
        $app = parent::createApplication();

        // Additional application setup if needed
        return $app;
    }

    protected function onNotSuccessfulTest(\Throwable $t): void
    {
        // Log errors
        $timestamp = date('Y-m-d_H-i-s');
        $errorMessage = sprintf(
            "Error in %s::%s: %s\n%s",
            static::class,
            $this->getName(),
            $t->getMessage(),
            $t->getTraceAsString()
        );
        file_put_contents(".errors/{$timestamp}.log", $errorMessage . PHP_EOL, FILE_APPEND);

        // Log failures
        if ($t instanceof \PHPUnit\Framework\AssertionFailedError) {
            $failureMessage = sprintf(
                "Failure in %s::%s: %s\n%s",
                static::class,
                $this->getName(),
                $t->getMessage(),
                $t->getTraceAsString()
            );
            file_put_contents(".failure/{$timestamp}.log", $failureMessage . PHP_EOL, FILE_APPEND);
        }

        parent::onNotSuccessfulTest($t);
    }
} 