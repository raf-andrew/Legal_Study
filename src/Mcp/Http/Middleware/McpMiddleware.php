<?php

namespace Mcp\Http\Middleware;

use Closure;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Config;
use Illuminate\Support\Facades\Log;

class McpMiddleware
{
    /**
     * Handle an incoming request.
     *
     * @param Request $request
     * @param Closure $next
     * @return mixed
     */
    public function handle(Request $request, Closure $next)
    {
        // Check if MCP is enabled
        if (!Config::get('mcp.enabled', false)) {
            Log::warning('MCP access attempted while disabled');
            abort(403, 'MCP is disabled');
        }

        // Check if current environment is allowed
        if (!in_array(app()->environment(), Config::get('mcp.environments', []))) {
            Log::warning('MCP access attempted from unauthorized environment: ' . app()->environment());
            abort(403, 'MCP is not available in this environment');
        }

        // Check authentication if required
        if (Config::get('mcp.security.auth.enabled', true)) {
            $this->authenticate($request);
        }

        // Check authorization if required
        if (Config::get('mcp.security.authorization.enabled', true)) {
            $this->authorize($request);
        }

        // Apply rate limiting if enabled
        if (Config::get('mcp.security.rate_limit.enabled', true)) {
            $this->rateLimit($request);
        }

        return $next($request);
    }

    /**
     * Authenticate the request.
     *
     * @param Request $request
     * @return void
     */
    protected function authenticate(Request $request): void
    {
        $driver = Config::get('mcp.security.auth.driver', 'session');
        $middleware = Config::get('mcp.security.auth.middleware', 'auth');

        if (!$request->user($driver)) {
            Log::warning('MCP authentication failed');
            abort(401, 'Unauthorized');
        }
    }

    /**
     * Authorize the request.
     *
     * @param Request $request
     * @return void
     */
    protected function authorize(Request $request): void
    {
        $policy = Config::get('mcp.security.authorization.policy');

        if ($policy && !app($policy)->access($request->user())) {
            Log::warning('MCP authorization failed');
            abort(403, 'Forbidden');
        }
    }

    /**
     * Apply rate limiting to the request.
     *
     * @param Request $request
     * @return void
     */
    protected function rateLimit(Request $request): void
    {
        $maxAttempts = Config::get('mcp.security.rate_limit.max_attempts', 60);
        $decayMinutes = Config::get('mcp.security.rate_limit.decay_minutes', 1);

        $key = $request->user()->id . '|' . $request->ip();

        if (app('cache')->has($key)) {
            $attempts = app('cache')->get($key);
            if ($attempts >= $maxAttempts) {
                Log::warning('MCP rate limit exceeded');
                abort(429, 'Too Many Requests');
            }
            app('cache')->increment($key);
        } else {
            app('cache')->put($key, 1, $decayMinutes * 60);
        }
    }
} 