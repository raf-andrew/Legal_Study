<?php

namespace LegalStudy\ModularInitialization\Contracts;

interface InitializationInterface
{
    /**
     * Validate the initialization configuration.
     *
     * @param array $config
     * @return bool
     * @throws \InvalidArgumentException
     */
    public function validateConfiguration(array $config): bool;

    /**
     * Test the connection or resource availability.
     *
     * @return bool
     * @throws \RuntimeException
     */
    public function testConnection(): bool;

    /**
     * Perform the initialization process.
     *
     * @return void
     * @throws \RuntimeException
     */
    public function performInitialization(): void;

    /**
     * Get the initialization status.
     *
     * @return InitializationStatusInterface
     */
    public function getStatus(): InitializationStatusInterface;

    /**
     * Get the current configuration.
     *
     * @return array
     */
    public function getConfig(): array;

    /**
     * Set the configuration.
     *
     * @param array $config
     * @return void
     */
    public function setConfig(array $config): void;
} 