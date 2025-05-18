<?php

namespace Tests\Mcp\Providers;

use Mcp\Providers\McpServiceProvider;
use Tests\TestCase;
use Illuminate\Support\Facades\Config;
use Illuminate\Support\Facades\Event;
use Illuminate\Support\Facades\Route;

class McpServiceProviderTest extends TestCase
{
    private McpServiceProvider $provider;

    protected function setUp(): void
    {
        parent::setUp();
        $this->provider = new McpServiceProvider($this->app);
    }

    public function testServiceRegistration(): void
    {
        $this->provider->register();

        $this->assertTrue($this->app->bound(\Mcp\Discovery\Discovery::class));
        $this->assertTrue($this->app->bound(\Mcp\Discovery\ServiceRegistry::class));
        $this->assertTrue($this->app->bound(\Mcp\Discovery\ServiceHealthMonitor::class));
    }

    public function testConfigurationLoading(): void
    {
        $this->provider->register();

        $this->assertTrue(Config::has('mcp'));
        $this->assertIsArray(Config::get('mcp'));
        $this->assertArrayHasKey('enabled', Config::get('mcp'));
        $this->assertArrayHasKey('environments', Config::get('mcp'));
        $this->assertArrayHasKey('security', Config::get('mcp'));
    }

    public function testEventListeners(): void
    {
        $this->provider->register();
        $this->provider->boot();

        $this->assertTrue(Event::hasListeners(\Mcp\Events\ServiceDiscovered::class));
        $this->assertTrue(Event::hasListeners(\Mcp\Events\ServiceHealthChanged::class));
        $this->assertTrue(Event::hasListeners(\Mcp\Events\ServiceError::class));
    }

    public function testRouteRegistration(): void
    {
        $this->provider->register();
        $this->provider->boot();

        $this->assertTrue(Route::has('mcp.discover'));
        $this->assertTrue(Route::has('mcp.monitor'));
        $this->assertTrue(Route::has('mcp.manage'));
    }

    public function testMiddlewareRegistration(): void
    {
        $this->provider->register();
        $this->provider->boot();

        $this->assertTrue($this->app['router']->hasMiddlewareGroup('mcp'));
        $this->assertTrue($this->app['router']->hasMiddleware('mcp.auth'));
        $this->assertTrue($this->app['router']->hasMiddleware('mcp.rate_limit'));
    }

    public function testCommandRegistration(): void
    {
        $this->provider->register();
        $this->provider->boot();

        $this->assertTrue($this->app->has(\Mcp\Console\Commands\McpDiscover::class));
        $this->assertTrue($this->app->has(\Mcp\Console\Commands\McpMonitor::class));
        $this->assertTrue($this->app->has(\Mcp\Console\Commands\McpStatus::class));
    }

    public function testViewRegistration(): void
    {
        $this->provider->register();
        $this->provider->boot();

        $this->assertTrue(view()->exists('mcp::dashboard'));
        $this->assertTrue(view()->exists('mcp::services'));
        $this->assertTrue(view()->exists('mcp::monitoring'));
    }

    public function testAssetPublishing(): void
    {
        $this->provider->register();
        $this->provider->boot();

        $this->assertTrue(file_exists(public_path('vendor/mcp/css/app.css')));
        $this->assertTrue(file_exists(public_path('vendor/mcp/js/app.js')));
    }
} 