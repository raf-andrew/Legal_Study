<?php

namespace App\Mcp\Core\Config;

use Illuminate\Support\Facades\File;
use Illuminate\Support\Facades\Log;
use Illuminate\Support\Facades\Storage;

class ConfigManager implements ConfigManagerInterface
{
    protected array $config = [];
    protected array $environmentConfigs = [];
    protected string $defaultEnvironment = 'default';

    public function load(string $source, array $options = []): bool
    {
        try {
            if (File::exists($source)) {
                $content = File::get($source);
                $this->config = json_decode($content, true) ?? [];
                return true;
            }

            if (Storage::exists($source)) {
                $content = Storage::get($source);
                $this->config = json_decode($content, true) ?? [];
                return true;
            }

            Log::warning("Configuration source not found: {$source}");
            return false;
        } catch (\Throwable $e) {
            Log::error("Error loading configuration from {$source}: " . $e->getMessage());
            return false;
        }
    }

    public function save(string $destination, array $options = []): bool
    {
        try {
            $content = json_encode($this->config, JSON_PRETTY_PRINT);
            
            if (str_starts_with($destination, 'storage/')) {
                return Storage::put($destination, $content);
            }

            return File::put($destination, $content);
        } catch (\Throwable $e) {
            Log::error("Error saving configuration to {$destination}: " . $e->getMessage());
            return false;
        }
    }

    public function get(string $key, mixed $default = null): mixed
    {
        $keys = explode('.', $key);
        $value = $this->config;

        foreach ($keys as $k) {
            if (!is_array($value) || !array_key_exists($k, $value)) {
                return $default;
            }
            $value = $value[$k];
        }

        return $value;
    }

    public function set(string $key, mixed $value): bool
    {
        try {
            $keys = explode('.', $key);
            $config = &$this->config;

            foreach ($keys as $k) {
                if (!isset($config[$k]) || !is_array($config[$k])) {
                    $config[$k] = [];
                }
                $config = &$config[$k];
            }

            $config = $value;
            return true;
        } catch (\Throwable $e) {
            Log::error("Error setting configuration key {$key}: " . $e->getMessage());
            return false;
        }
    }

    public function has(string $key): bool
    {
        $keys = explode('.', $key);
        $value = $this->config;

        foreach ($keys as $k) {
            if (!is_array($value) || !array_key_exists($k, $value)) {
                return false;
            }
            $value = $value[$k];
        }

        return true;
    }

    public function remove(string $key): bool
    {
        try {
            $keys = explode('.', $key);
            $config = &$this->config;

            foreach ($keys as $k) {
                if (!isset($config[$k])) {
                    return false;
                }
                if (count($keys) === 1) {
                    unset($config[$k]);
                    return true;
                }
                $config = &$config[$k];
            }

            return false;
        } catch (\Throwable $e) {
            Log::error("Error removing configuration key {$key}: " . $e->getMessage());
            return false;
        }
    }

    public function all(): array
    {
        return $this->config;
    }

    public function clear(): bool
    {
        try {
            $this->config = [];
            return true;
        } catch (\Throwable $e) {
            Log::error("Error clearing configuration: " . $e->getMessage());
            return false;
        }
    }

    public function validate(array $schema): array
    {
        $errors = [];
        
        foreach ($schema as $key => $rules) {
            $value = $this->get($key);
            
            if (isset($rules['required']) && $rules['required'] && $value === null) {
                $errors[$key][] = 'Required field is missing';
                continue;
            }
            
            if ($value === null) {
                continue;
            }
            
            if (isset($rules['type'])) {
                $type = gettype($value);
                if ($type !== $rules['type']) {
                    $errors[$key][] = "Expected type {$rules['type']}, got {$type}";
                }
            }
            
            if (isset($rules['enum']) && !in_array($value, $rules['enum'])) {
                $errors[$key][] = "Value must be one of: " . implode(', ', $rules['enum']);
            }
            
            if (isset($rules['min']) && $value < $rules['min']) {
                $errors[$key][] = "Value must be at least {$rules['min']}";
            }
            
            if (isset($rules['max']) && $value > $rules['max']) {
                $errors[$key][] = "Value must be at most {$rules['max']}";
            }
        }
        
        return $errors;
    }

    public function getEnvironmentConfig(string $environment): array
    {
        return $this->environmentConfigs[$environment] ?? [];
    }

    public function setEnvironmentConfig(string $environment, array $config): bool
    {
        try {
            $this->environmentConfigs[$environment] = $config;
            return true;
        } catch (\Throwable $e) {
            Log::error("Error setting environment configuration for {$environment}: " . $e->getMessage());
            return false;
        }
    }
} 