<?php

namespace LegalStudy\Console\Tests\Mocks;

interface MockServiceInterface
{
    /**
     * Get the service name
     *
     * @return string
     */
    public function getName(): string;

    /**
     * Check if the service is available
     *
     * @return bool
     */
    public function isAvailable(): bool;

    /**
     * Get the service status
     *
     * @return array
     */
    public function getStatus(): array;

    /**
     * Get the service configuration
     *
     * @return array
     */
    public function getConfig(): array;

    /**
     * Set the service configuration
     *
     * @param array $config
     * @return void
     */
    public function setConfig(array $config): void;

    /**
     * Reset the service to its initial state
     *
     * @return void
     */
    public function reset(): void;

    /**
     * Enable the service
     *
     * @return void
     */
    public function enable(): void;

    /**
     * Disable the service
     *
     * @return void
     */
    public function disable(): void;

    /**
     * Set the service to fail
     *
     * @param bool $shouldFail
     * @return void
     */
    public function setShouldFail(bool $shouldFail): void;

    /**
     * Check if the service should fail
     *
     * @return bool
     */
    public function shouldFail(): bool;
} 