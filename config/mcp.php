<?php

return [
    /*
    |--------------------------------------------------------------------------
    | MCP Server Configuration
    |--------------------------------------------------------------------------
    |
    | This file contains the configuration for the Master Control Program (MCP)
    | server. The MCP server provides development and monitoring capabilities
    | for the application.
    |
    */

    'enabled' => env('MCP_ENABLED', false),
    'debug' => env('MCP_DEBUG', false),

    /*
    |--------------------------------------------------------------------------
    | Security Settings
    |--------------------------------------------------------------------------
    |
    | Configure security settings for the MCP server. In production, these
    | settings should be carefully configured to prevent unauthorized access.
    |
    */
    'security' => [
        'enabled' => env('MCP_SECURITY_ENABLED', true),
        'allowed_ips' => explode(',', env('MCP_ALLOWED_IPS', '')),
        'api_key' => env('MCP_API_KEY', null),
    ],

    /*
    |--------------------------------------------------------------------------
    | Monitoring Settings
    |--------------------------------------------------------------------------
    |
    | Configure monitoring settings for the MCP server. These settings control
    | how often metrics are collected and what metrics are monitored.
    |
    */
    'monitoring' => [
        'interval' => env('MCP_MONITORING_INTERVAL', 60),
        'metrics' => [
            'cpu',
            'memory',
            'disk',
            'network',
        ],
    ],

    /*
    |--------------------------------------------------------------------------
    | Services Configuration
    |--------------------------------------------------------------------------
    |
    | Configure the services that the MCP server will manage. Each service
    | can have its own configuration and monitoring settings.
    |
    */
    'services' => [
        // Example service configuration
        // 'example_service' => [
        //     'enabled' => true,
        //     'monitoring' => [
        //         'interval' => 30,
        //         'metrics' => ['cpu', 'memory'],
        //     ],
        // ],
    ],

    /*
    |--------------------------------------------------------------------------
    | Logging Settings
    |--------------------------------------------------------------------------
    |
    | Configure logging settings for the MCP server. These settings control
    | how and where MCP server logs are stored.
    |
    */
    'logging' => [
        'enabled' => env('MCP_LOGGING_ENABLED', true),
        'level' => env('MCP_LOG_LEVEL', 'info'),
        'channel' => env('MCP_LOG_CHANNEL', 'stack'),
    ],

    /*
    |--------------------------------------------------------------------------
    | Development Tools
    |--------------------------------------------------------------------------
    |
    | Configure development tools that are available through the MCP server.
    | These tools are only available in non-production environments.
    |
    */
    'development_tools' => [
        'enabled' => !env('APP_ENV', 'local') === 'production',
        'tools' => [
            'debugger' => true,
            'profiler' => true,
            'inspector' => true,
        ],
    ],
]; 