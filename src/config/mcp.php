<?php

return [
    /*
    |--------------------------------------------------------------------------
    | MCP Server Configuration
    |--------------------------------------------------------------------------
    |
    | This file contains the configuration for the MCP (Master Control Program)
    | server. The MCP server provides agentic capabilities and development
    | assistance within the platform.
    |
    */

    'enabled' => env('MCP_ENABLED', false),

    'development_mode' => env('APP_ENV') === 'local',

    'security' => [
        'require_authentication' => env('MCP_REQUIRE_AUTH', true),
        'allowed_origins' => explode(',', env('MCP_ALLOWED_ORIGINS', '')),
        'rate_limit' => env('MCP_RATE_LIMIT', 100),
    ],

    'features' => [
        'agentic' => env('MCP_FEATURE_AGENTIC', true),
        'development' => env('MCP_FEATURE_DEVELOPMENT', true),
        'monitoring' => env('MCP_FEATURE_MONITORING', true),
    ],

    'logging' => [
        'enabled' => env('MCP_LOGGING_ENABLED', true),
        'level' => env('MCP_LOGGING_LEVEL', 'debug'),
        'channels' => ['stack'],
    ],

    'services' => [
        'discovery' => [
            'enabled' => true,
            'interval' => 60, // seconds
        ],
        'monitoring' => [
            'enabled' => true,
            'interval' => 30, // seconds
        ],
    ],
]; 