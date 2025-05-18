<?php

namespace App\Mcp;

use Illuminate\Support\Facades\Auth;
use Illuminate\Support\Facades\Log;
use Illuminate\Support\Facades\RateLimiter;
use Illuminate\Support\Str;

class SecurityManager
{
    protected $config;
    protected $tokens = [];
    protected $rateLimiter;

    public function __construct()
    {
        $this->config = app(ConfigurationManager::class)->getSecurityConfig();
        $this->rateLimiter = app(RateLimiter::class);
    }

    public function authenticate($credentials)
    {
        if (!$this->config['require_authentication']) {
            return true;
        }

        if (Auth::attempt($credentials)) {
            $token = $this->generateToken();
            $this->tokens[$token] = [
                'user_id' => Auth::id(),
                'created_at' => now(),
                'expires_at' => now()->addHours(1)
            ];

            Log::info("MCP Authentication successful for user: " . Auth::id());
            return $token;
        }

        Log::warning("MCP Authentication failed");
        return false;
    }

    public function validateToken($token)
    {
        if (!$this->config['require_authentication']) {
            return true;
        }

        if (!isset($this->tokens[$token])) {
            return false;
        }

        $tokenData = $this->tokens[$token];
        if (now()->gt($tokenData['expires_at'])) {
            unset($this->tokens[$token]);
            return false;
        }

        return true;
    }

    public function checkRateLimit($identifier)
    {
        $limit = $this->config['rate_limit'];
        $key = 'mcp:' . $identifier;

        if ($this->rateLimiter->tooManyAttempts($key, $limit)) {
            Log::warning("MCP Rate limit exceeded for: {$identifier}");
            return false;
        }

        $this->rateLimiter->hit($key);
        return true;
    }

    public function validateOrigin($origin)
    {
        $allowedOrigins = $this->config['allowed_origins'];
        
        if (empty($allowedOrigins)) {
            return true;
        }

        return in_array($origin, $allowedOrigins);
    }

    public function revokeToken($token)
    {
        if (isset($this->tokens[$token])) {
            unset($this->tokens[$token]);
            Log::info("MCP Token revoked: {$token}");
            return true;
        }

        return false;
    }

    protected function generateToken()
    {
        return Str::random(64);
    }

    public function getTokenData($token)
    {
        return $this->tokens[$token] ?? null;
    }

    public function cleanupExpiredTokens()
    {
        $now = now();
        foreach ($this->tokens as $token => $data) {
            if ($now->gt($data['expires_at'])) {
                unset($this->tokens[$token]);
            }
        }
    }
} 