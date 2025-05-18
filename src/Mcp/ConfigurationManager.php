<?php

namespace App\Mcp;

use Illuminate\Support\Facades\Config;
use Illuminate\Support\Facades\Log;

class ConfigurationManager
{
    protected $config = [];
    protected $defaults = [
        'enabled' => false,
        'development_mode' => false,
        'security' => [
            'require_authentication' => true,
            'allowed_origins' => [],
            'rate_limit' => 100,
        ],
        'features' => [
            'agentic' => true,
            'development' => true,
            'monitoring' => true,
        ],
        'services' => [
            'discovery' => [
                'enabled' => true,
                'interval' => 60,
                'paths' => [
                    'app/Services',
                    'app/Http/Controllers',
                    'app/Console/Commands',
                ],
            ],
        ],
    ];

    public function __construct()
    {
        $this->loadConfiguration();
    }

    protected function loadConfiguration()
    {
        $this->config = array_merge(
            $this->defaults,
            Config::get('mcp', [])
        );

        // Override development mode based on environment
        $this->config['development_mode'] = Config::get('app.env') === 'local';
        
        Log::info("MCP Configuration loaded");
    }

    public function get($key = null, $default = null)
    {
        if ($key === null) {
            return $this->config;
        }

        $keys = explode('.', $key);
        $value = $this->config;

        foreach ($keys as $k) {
            if (!isset($value[$k])) {
                return $default;
            }
            $value = $value[$k];
        }

        return $value;
    }

    public function set($key, $value)
    {
        $keys = explode('.', $key);
        $config = &$this->config;

        foreach ($keys as $k) {
            if (!isset($config[$k]) || !is_array($config[$k])) {
                $config[$k] = [];
            }
            $config = &$config[$k];
        }

        $config = $value;
        Log::info("MCP Configuration updated: {$key}");
    }

    public function isEnabled()
    {
        return $this->get('enabled');
    }

    public function isDevelopmentMode()
    {
        return $this->get('development_mode');
    }

    public function isFeatureEnabled($feature)
    {
        return $this->get("features.{$feature}", false);
    }

    public function getSecurityConfig()
    {
        return $this->get('security');
    }

    public function getServicesConfig()
    {
        return $this->get('services');
    }

    public function validateConfiguration()
    {
        $errors = [];

        // Validate required settings
        if (!isset($this->config['enabled'])) {
            $errors[] = 'Missing required configuration: enabled';
        }

        if (!isset($this->config['security'])) {
            $errors[] = 'Missing required configuration: security';
        }

        if (!isset($this->config['features'])) {
            $errors[] = 'Missing required configuration: features';
        }

        // Validate security settings
        if (isset($this->config['security'])) {
            if (!isset($this->config['security']['require_authentication'])) {
                $errors[] = 'Missing required security configuration: require_authentication';
            }

            if (!isset($this->config['security']['allowed_origins'])) {
                $errors[] = 'Missing required security configuration: allowed_origins';
            }

            if (!isset($this->config['security']['rate_limit'])) {
                $errors[] = 'Missing required security configuration: rate_limit';
            }
        }

        // Log validation results
        if (!empty($errors)) {
            Log::error('MCP Configuration validation failed: ' . implode(', ', $errors));
        } else {
            Log::info('MCP Configuration validation passed');
        }

        return $errors;
    }
} 