<?php

return [
    /*
    |--------------------------------------------------------------------------
    | Default Initialization Settings
    |--------------------------------------------------------------------------
    |
    | These are the default settings for the initialization process.
    |
    */

    'permissions' => 0755,

    /*
    |--------------------------------------------------------------------------
    | Required Directories
    |--------------------------------------------------------------------------
    |
    | These directories will be created during the initialization process.
    |
    */

    'required_dirs' => [
        'cache',
        'logs',
        'uploads',
    ],

    /*
    |--------------------------------------------------------------------------
    | Initialization Order
    |--------------------------------------------------------------------------
    |
    | The order in which initializations should be performed.
    |
    */

    'initialization_order' => [
        'filesystem',
        'cache',
        'database',
        'queue',
    ],

    /*
    |--------------------------------------------------------------------------
    | Error Handling
    |--------------------------------------------------------------------------
    |
    | Configure how errors should be handled during initialization.
    |
    */

    'error_handling' => [
        'throw_exceptions' => true,
        'log_errors' => true,
    ],

    /*
    |--------------------------------------------------------------------------
    | Performance Monitoring
    |--------------------------------------------------------------------------
    |
    | Configure performance monitoring settings.
    |
    */

    'performance_monitoring' => [
        'enabled' => true,
        'threshold_ms' => 1000,
    ],
]; 