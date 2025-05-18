<?php

namespace Tests\Feature;

use Tests\TestCase;
use App\Models\User;
use Laravel\Sanctum\Sanctum;
use Illuminate\Support\Facades\Route;
use Illuminate\Support\Facades\Config;

abstract class RouteTestCase extends TestCase
{
    protected $user;
    protected $route;
    protected $method;
    protected $requiresAuth = false;

    protected function setUp(): void
    {
        parent::setUp();

        // Create test user if authentication is required
        if ($this->requiresAuth) {
            $this->user = User::factory()->create([
                'name' => 'Test User',
                'email' => 'test@example.com'
            ]);
            Sanctum::actingAs($this->user);
        }

        // Enable route caching for performance testing
        Config::set('app.env', 'testing');
        Route::enableRouteCache();
    }

    protected function tearDown(): void
    {
        // Clear route cache
        Route::clearResolvedInstances();
        Route::clearCache();

        parent::tearDown();
    }

    protected function assertRouteExists()
    {
        $this->assertTrue(
            Route::has($this->route),
            "Route {$this->route} does not exist"
        );
    }

    protected function assertRouteRequiresAuth()
    {
        $this->assertTrue(
            $this->requiresAuth,
            "Route {$this->route} should require authentication"
        );
    }

    protected function assertRouteMethod()
    {
        $route = Route::getRoutes()->getByName($this->route);
        $this->assertEquals(
            strtoupper($this->method),
            $route->methods()[0],
            "Route {$this->route} should use {$this->method} method"
        );
    }

    protected function assertRoutePerformance()
    {
        $this->assertPerformance(function () {
            $this->call($this->method, $this->route);
        }, 0.5); // 500ms threshold
    }

    protected function assertRouteRateLimited()
    {
        // Make multiple requests in quick succession
        for ($i = 0; $i < 60; $i++) {
            $this->call($this->method, $this->route);
        }

        // The next request should be rate limited
        $response = $this->call($this->method, $this->route);
        $this->assertRateLimited($response);
    }

    protected function assertRouteValidation($data, $rules)
    {
        $response = $this->call($this->method, $this->route, $data);

        foreach ($rules as $field => $rule) {
            $this->assertValidationError($response, $field);
        }
    }

    protected function assertRouteResponse($expectedStatus = 200, $expectedData = null)
    {
        $response = $this->call($this->method, $this->route);

        if ($expectedStatus === 200) {
            $this->assertSuccessResponse($response, $expectedData);
        } else {
            $this->assertErrorResponse($response, $expectedStatus);
        }
    }

    protected function getRouteCoverage()
    {
        $coverage = parent::getCoverageData();
        $coverage['route'] = $this->route;
        $coverage['method'] = $this->method;
        $coverage['requires_auth'] = $this->requiresAuth;

        return $coverage;
    }
}
