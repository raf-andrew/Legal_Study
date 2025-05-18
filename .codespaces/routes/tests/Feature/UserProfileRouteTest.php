<?php

namespace Tests\Feature;

class UserProfileRouteTest extends RouteTestCase
{
    protected $route = 'user';
    protected $method = 'GET';
    protected $requiresAuth = true;

    public function test_user_profile_route_exists()
    {
        $this->assertRouteExists();
    }

    public function test_user_profile_requires_auth()
    {
        $this->assertRouteRequiresAuth();
    }

    public function test_user_profile_returns_200()
    {
        $this->assertRouteResponse(200, [
            'id' => $this->user->id,
            'name' => 'Test User',
            'email' => 'test@example.com'
        ]);
    }

    public function test_unauthenticated_user_cannot_access_profile()
    {
        // Clear authentication
        auth()->logout();

        $this->assertRouteResponse(401, [
            'message' => 'Unauthenticated.'
        ]);
    }

    public function test_user_profile_performance()
    {
        $this->assertRoutePerformance();
    }

    public function test_user_profile_rate_limiting()
    {
        $this->assertRouteRateLimited();
    }
}
