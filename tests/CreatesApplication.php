<?php

namespace Tests;

use Illuminate\Contracts\Console\Kernel;
use Illuminate\Foundation\Application;

trait CreatesApplication
{
    /**
     * Creates the application.
     *
     * @return Application
     */
    public function createApplication(): Application
    {
        $app = require __DIR__.'/../bootstrap/app.php';

        $app->make(Kernel::class)->bootstrap();

        return $app;
    }

    /**
     * Boot the testing environment.
     */
    protected function bootTestingEnvironment(): void
    {
        // Set the environment to testing
        putenv('APP_ENV=testing');

        // Clear the cache
        $this->clearCache();

        // Bootstrap the application
        $this->app = $this->createApplication();

        // Set up the test environment
        $this->setUpTestEnvironment();
    }

    /**
     * Clear the cache.
     */
    protected function clearCache(): void
    {
        $commands = [
            'cache:clear',
            'config:clear',
            'route:clear',
            'view:clear',
        ];

        foreach ($commands as $command) {
            \Illuminate\Support\Facades\Artisan::call($command);
        }
    }

    /**
     * Set up the test environment.
     */
    protected function setUpTestEnvironment(): void
    {
        // Set up test database
        $this->setUpTestDatabase();

        // Set up test configuration
        $this->setUpTestConfiguration();

        // Set up test services
        $this->setUpTestServices();
    }

    /**
     * Set up the test database.
     */
    protected function setUpTestDatabase(): void
    {
        // Use SQLite for testing
        config(['database.default' => 'sqlite']);
        config(['database.connections.sqlite.database' => ':memory:']);

        // Run migrations
        \Illuminate\Support\Facades\Artisan::call('migrate:fresh');
    }

    /**
     * Set up test configuration.
     */
    protected function setUpTestConfiguration(): void
    {
        // Disable MCP in production
        config(['mcp.enabled' => !app()->environment('production')]);

        // Set test-specific configuration
        config([
            'app.debug' => true,
            'app.env' => 'testing',
            'cache.default' => 'array',
            'session.driver' => 'array',
            'queue.default' => 'sync',
        ]);
    }

    /**
     * Set up test services.
     */
    protected function setUpTestServices(): void
    {
        // Register test service providers
        $this->app->register(\Mcp\Providers\McpServiceProvider::class);

        // Bind test implementations
        $this->app->bind(
            \Mcp\Discovery\Discovery::class,
            \Mcp\Discovery\Discovery::class
        );

        $this->app->bind(
            \Mcp\Discovery\ServiceRegistry::class,
            \Mcp\Discovery\ServiceRegistry::class
        );

        $this->app->bind(
            \Mcp\Discovery\ServiceHealthMonitor::class,
            \Mcp\Discovery\ServiceHealthMonitor::class
        );
    }
}
