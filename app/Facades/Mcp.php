<?php

namespace App\Facades;

use Illuminate\Support\Facades\Facade;

/**
 * @method static bool isEnabled()
 * @method static bool isProduction()
 * @method static array getConfig()
 * @method static array getHealthMetrics()
 * @method static array getServices()
 * @method static bool registerService(string $name, array $config)
 * 
 * @see \App\Mcp\Core\Server
 */
class Mcp extends Facade
{
    protected static function getFacadeAccessor(): string
    {
        return \App\Mcp\Core\Server::class;
    }
} 