<?php

namespace LegalStudy\ModularInitialization\Contracts;

interface InitializationStatusInterface
{
    /**
     * Check if initialization is complete.
     *
     * @return bool
     */
    public function isInitialized(): bool;

    /**
     * Set the initialization status.
     *
     * @param bool $status
     * @return void
     */
    public function setInitialized(bool $status): void;

    /**
     * Check if initialization has failed.
     *
     * @return bool
     */
    public function isFailed(): bool;

    /**
     * Add an error message.
     *
     * @param string $error
     * @return void
     */
    public function addError(string $error): void;

    /**
     * Get all error messages.
     *
     * @return array
     */
    public function getErrors(): array;

    /**
     * Add data to the status.
     *
     * @param string $key
     * @param mixed $value
     * @return void
     */
    public function addData(string $key, mixed $value): void;

    /**
     * Get data from the status.
     *
     * @param string $key
     * @return mixed
     */
    public function getData(string $key): mixed;

    /**
     * Get all status data.
     *
     * @return array
     */
    public function getAllData(): array;

    /**
     * Reset the status.
     *
     * @return void
     */
    public function reset(): void;
} 