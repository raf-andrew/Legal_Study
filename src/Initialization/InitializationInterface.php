<?php

namespace LegalStudy\Initialization;

interface InitializationInterface
{
    /**
     * Validate initialization configuration
     *
     * @param array $config Configuration array
     * @throws \RuntimeException If configuration is invalid
     */
    public function validateConfiguration(array $config): void;

    /**
     * Test connection to the required service
     *
     * @return bool True if connection is successful, false otherwise
     */
    public function testConnection(): bool;

    /**
     * Perform initialization
     *
     * @throws \RuntimeException If initialization fails
     */
    public function performInitialization(): void;

    /**
     * Get initialization status
     *
     * @return InitializationStatus Current initialization status
     */
    public function getStatus(): InitializationStatus;

    /**
     * Set initialization status
     *
     * @param InitializationStatus $status New initialization status
     */
    public function setStatus(InitializationStatus $status): void;
} 