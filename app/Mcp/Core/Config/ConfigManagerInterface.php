<?php

namespace App\Mcp\Core\Config;

interface ConfigManagerInterface
{
    /**
     * Load configuration from a source.
     *
     * @param string $source The source to load configuration from
     * @param array $options Additional options for loading
     * @return bool True if configuration was loaded successfully
     */
    public function load(string $source, array $options = []): bool;

    /**
     * Save configuration to a destination.
     *
     * @param string $destination The destination to save configuration to
     * @param array $options Additional options for saving
     * @return bool True if configuration was saved successfully
     */
    public function save(string $destination, array $options = []): bool;

    /**
     * Get a configuration value.
     *
     * @param string $key The configuration key
     * @param mixed $default The default value if key is not found
     * @return mixed The configuration value
     */
    public function get(string $key, mixed $default = null): mixed;

    /**
     * Set a configuration value.
     *
     * @param string $key The configuration key
     * @param mixed $value The configuration value
     * @return bool True if the value was set successfully
     */
    public function set(string $key, mixed $value): bool;

    /**
     * Check if a configuration key exists.
     *
     * @param string $key The configuration key
     * @return bool True if the key exists
     */
    public function has(string $key): bool;

    /**
     * Remove a configuration key.
     *
     * @param string $key The configuration key
     * @return bool True if the key was removed successfully
     */
    public function remove(string $key): bool;

    /**
     * Get all configuration values.
     *
     * @return array All configuration values
     */
    public function all(): array;

    /**
     * Clear all configuration values.
     *
     * @return bool True if configuration was cleared successfully
     */
    public function clear(): bool;

    /**
     * Validate configuration against a schema.
     *
     * @param array $schema The validation schema
     * @return array Validation errors, empty if valid
     */
    public function validate(array $schema): array;

    /**
     * Get environment-specific configuration.
     *
     * @param string $environment The environment name
     * @return array Environment-specific configuration
     */
    public function getEnvironmentConfig(string $environment): array;

    /**
     * Set environment-specific configuration.
     *
     * @param string $environment The environment name
     * @param array $config The configuration to set
     * @return bool True if configuration was set successfully
     */
    public function setEnvironmentConfig(string $environment, array $config): bool;
} 