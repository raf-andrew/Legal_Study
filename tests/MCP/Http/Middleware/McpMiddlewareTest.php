<?php

namespace Tests\Mcp\Http\Middleware;

use Mcp\Http\Middleware\McpMiddleware;
use Tests\TestCase;
use Illuminate\Support\Facades\Config;
use Illuminate\Support\Facades\Auth;
use Illuminate\Http\Request;
use Illuminate\Http\Response;
use Mockery;

class McpMiddlewareTest extends TestCase
{
    private McpMiddleware $middleware;

    protected function setUp(): void
    {
        parent::setUp();
        $this->middleware = new McpMiddleware();
    }

    public function testHandleWithMcpDisabled(): void
    {
        Config::set('mcp.enabled', false);

        $request = new Request();
        $next = function ($request) {
            return new Response('Success');
        };

        $response = $this->middleware->handle($request, $next);
        
        $this->assertEquals(403, $response->getStatusCode());
        $this->assertEquals('MCP is disabled', $response->getContent());
    }

    public function testHandleWithEnvironmentNotAllowed(): void
    {
        Config::set('mcp.enabled', true);
        Config::set('mcp.environments', ['production']);

        $request = new Request();
        $next = function ($request) {
            return new Response('Success');
        };

        $response = $this->middleware->handle($request, $next);
        
        $this->assertEquals(403, $response->getStatusCode());
        $this->assertEquals('MCP is not available in this environment', $response->getContent());
    }

    public function testHandleWithAuthenticationRequired(): void
    {
        Config::set('mcp.enabled', true);
        Config::set('mcp.environments', ['testing']);
        Config::set('mcp.security.require_auth', true);

        $request = new Request();
        $next = function ($request) {
            return new Response('Success');
        };

        $response = $this->middleware->handle($request, $next);
        
        $this->assertEquals(401, $response->getStatusCode());
        $this->assertEquals('Unauthorized', $response->getContent());
    }

    public function testHandleWithAuthenticationPassed(): void
    {
        Config::set('mcp.enabled', true);
        Config::set('mcp.environments', ['testing']);
        Config::set('mcp.security.require_auth', true);

        $user = Mockery::mock('Illuminate\Contracts\Auth\Authenticatable');
        Auth::shouldReceive('check')
            ->once()
            ->andReturn(true);
        Auth::shouldReceive('user')
            ->once()
            ->andReturn($user);

        $request = new Request();
        $next = function ($request) {
            return new Response('Success');
        };

        $response = $this->middleware->handle($request, $next);
        
        $this->assertEquals(200, $response->getStatusCode());
        $this->assertEquals('Success', $response->getContent());
    }

    public function testHandleWithAuthorizationRequired(): void
    {
        Config::set('mcp.enabled', true);
        Config::set('mcp.environments', ['testing']);
        Config::set('mcp.security.require_auth', true);
        Config::set('mcp.security.require_roles', ['admin']);

        $user = Mockery::mock('Illuminate\Contracts\Auth\Authenticatable');
        $user->shouldReceive('hasRole')
            ->once()
            ->with('admin')
            ->andReturn(false);

        Auth::shouldReceive('check')
            ->once()
            ->andReturn(true);
        Auth::shouldReceive('user')
            ->once()
            ->andReturn($user);

        $request = new Request();
        $next = function ($request) {
            return new Response('Success');
        };

        $response = $this->middleware->handle($request, $next);
        
        $this->assertEquals(403, $response->getStatusCode());
        $this->assertEquals('Forbidden', $response->getContent());
    }

    public function testHandleWithAuthorizationPassed(): void
    {
        Config::set('mcp.enabled', true);
        Config::set('mcp.environments', ['testing']);
        Config::set('mcp.security.require_auth', true);
        Config::set('mcp.security.require_roles', ['admin']);

        $user = Mockery::mock('Illuminate\Contracts\Auth\Authenticatable');
        $user->shouldReceive('hasRole')
            ->once()
            ->with('admin')
            ->andReturn(true);

        Auth::shouldReceive('check')
            ->once()
            ->andReturn(true);
        Auth::shouldReceive('user')
            ->once()
            ->andReturn($user);

        $request = new Request();
        $next = function ($request) {
            return new Response('Success');
        };

        $response = $this->middleware->handle($request, $next);
        
        $this->assertEquals(200, $response->getStatusCode());
        $this->assertEquals('Success', $response->getContent());
    }

    public function testHandleWithRateLimiting(): void
    {
        Config::set('mcp.enabled', true);
        Config::set('mcp.environments', ['testing']);
        Config::set('mcp.security.rate_limit', 1);

        $request = new Request();
        $next = function ($request) {
            return new Response('Success');
        };

        // First request should succeed
        $response = $this->middleware->handle($request, $next);
        $this->assertEquals(200, $response->getStatusCode());
        $this->assertEquals('Success', $response->getContent());

        // Second request should be rate limited
        $response = $this->middleware->handle($request, $next);
        $this->assertEquals(429, $response->getStatusCode());
        $this->assertEquals('Too Many Requests', $response->getContent());
    }
} 