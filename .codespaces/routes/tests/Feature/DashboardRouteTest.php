<?php

namespace Tests\Feature;

class DashboardRouteTest extends RouteTestCase
{
    protected $route = 'dashboard';
    protected $method = 'GET';
    protected $requiresAuth = true;

    public function test_dashboard_route_exists()
    {
        $this->assertRouteExists();
    }

    public function test_dashboard_requires_auth()
    {
        $this->assertRouteRequiresAuth();
    }

    public function test_dashboard_returns_200()
    {
        $this->assertRouteResponse(200);
    }

    public function test_unauthenticated_user_cannot_access_dashboard()
    {
        // Clear authentication
        auth()->logout();

        $this->assertRouteResponse(401, [
            'message' => 'Unauthenticated.'
        ]);
    }

    public function test_dashboard_performance()
    {
        $this->assertRoutePerformance();
    }

    public function test_dashboard_rate_limiting()
    {
        $this->assertRouteRateLimited();
    }
}
