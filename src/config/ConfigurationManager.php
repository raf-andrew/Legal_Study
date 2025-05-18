<?php

namespace App\Config;

use Illuminate\Support\Arr;
use Illuminate\Support\Facades\Cache;
use Illuminate\Support\Facades\Validator;
use Symfony\Component\Yaml\Yaml;

class ConfigurationManager
{
    private array $config = [];
    private array $schema = [];
    private string $environment;
    private array $overrides = [];

    public function __construct(string $environment = null)
    {
        $this->environment = $environment ?? app()->environment();
        $this->loadSchema();
    }

    public function load(string $configPath): void
    {
        if (!file_exists($configPath)) {
            throw new \RuntimeException("Configuration file not found: {$configPath}");
        }

        $extension = pathinfo($configPath, PATHINFO_EXTENSION);
        $config = match ($extension) {
            'yaml', 'yml' => Yaml::parseFile($configPath),
            'json' => json_decode(file_get_contents($configPath), true),
            'php' => require $configPath,
            default => throw new \RuntimeException("Unsupported configuration format: {$extension}")
        };

        if (!is_array($config)) {
            throw new \RuntimeException("Invalid configuration format");
        }

        // Merge with environment-specific configuration if available
        $envConfig = $this->loadEnvironmentConfig($configPath);
        $this->config = array_merge($config, $envConfig ?? [], $this->overrides);

        $this->validateConfiguration();
        $this->cacheConfiguration();
    }

    private function loadEnvironmentConfig(string $basePath): ?array
    {
        $pathInfo = pathinfo($basePath);
        $envPath = sprintf(
            "%s/%s.%s.%s",
            $pathInfo['dirname'],
            $pathInfo['filename'],
            $this->environment,
            $pathInfo['extension']
        );

        if (!file_exists($envPath)) {
            return null;
        }

        $extension = pathinfo($envPath, PATHINFO_EXTENSION);
        return match ($extension) {
            'yaml', 'yml' => Yaml::parseFile($envPath),
            'json' => json_decode(file_get_contents($envPath), true),
            'php' => require $envPath,
            default => null
        };
    }

    private function loadSchema(): void
    {
        $schemaPath = config('mcp.schema_path', base_path('config/schema.yaml'));
        if (!file_exists($schemaPath)) {
            return;
        }

        $this->schema = Yaml::parseFile($schemaPath);
    }

    private function validateConfiguration(): void
    {
        if (empty($this->schema)) {
            return;
        }

        $validator = Validator::make($this->config, $this->schema);
        if ($validator->fails()) {
            throw new \RuntimeException(
                "Configuration validation failed:\n" . 
                implode("\n", $validator->errors()->all())
            );
        }
    }

    private function cacheConfiguration(): void
    {
        $cacheKey = "mcp_config:{$this->environment}";
        Cache::put($cacheKey, $this->config, now()->addDay());
    }

    public function get(string $key, $default = null)
    {
        return Arr::get($this->config, $key, $default);
    }

    public function set(string $key, $value): void
    {
        Arr::set($this->config, $key, $value);
        $this->overrides[$key] = $value;
        $this->validateConfiguration();
        $this->cacheConfiguration();
    }

    public function has(string $key): bool
    {
        return Arr::has($this->config, $key);
    }

    public function all(): array
    {
        return $this->config;
    }

    public function getEnvironment(): string
    {
        return $this->environment;
    }

    public function merge(array $config): void
    {
        $this->config = array_merge_recursive($this->config, $config);
        $this->validateConfiguration();
        $this->cacheConfiguration();
    }

    public function reset(): void
    {
        $this->config = [];
        $this->overrides = [];
        Cache::forget("mcp_config:{$this->environment}");
    }
} 