<?php

return [
    /*
    |--------------------------------------------------------------------------
    | Codespaces Configuration
    |--------------------------------------------------------------------------
    |
    | This file contains the configuration for GitHub Codespaces integration.
    |
    */

    'enabled' => env('CODESPACES_ENABLED', false),

    'paths' => [
        'root' => '.codespaces',
        'logs' => base_path('.codespaces/logs'),
        'data' => base_path('.codespaces/data'),
        'complete' => base_path('.codespaces/complete'),
        'services' => base_path('.codespaces/services'),
    ],

    'services' => [
        'mysql' => [
            'enabled' => env('CODESPACES_MYSQL_ENABLED', true),
            'host' => env('CODESPACES_MYSQL_HOST', 'localhost'),
            'port' => env('CODESPACES_MYSQL_PORT', 3306),
            'database' => env('CODESPACES_MYSQL_DATABASE', 'codespaces'),
            'username' => env('CODESPACES_MYSQL_USERNAME', 'root'),
            'password' => env('CODESPACES_MYSQL_PASSWORD', ''),
        ],
        'redis' => [
            'enabled' => env('CODESPACES_REDIS_ENABLED', true),
            'host' => env('CODESPACES_REDIS_HOST', 'localhost'),
            'port' => env('CODESPACES_REDIS_PORT', 6379),
            'password' => env('CODESPACES_REDIS_PASSWORD', null),
        ],
    ],

    'health_check' => [
        'interval' => env('CODESPACES_HEALTH_CHECK_INTERVAL', 60), // seconds
        'timeout' => env('CODESPACES_HEALTH_CHECK_TIMEOUT', 5), // seconds
    ],

    'logging' => [
        'enabled' => true,
        'channels' => [
            'codespaces' => [
                'driver' => 'daily',
                'path' => storage_path('logs/codespaces.log'),
                'level' => env('CODESPACES_LOG_LEVEL', 'debug'),
                'days' => 14,
            ],
        ],
    ],

    'database' => [
        'path' => base_path('.codespaces/data/codespaces.db'),
    ],
];
