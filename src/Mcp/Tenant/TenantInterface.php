<?php

namespace Mcp\Tenant;

interface TenantInterface
{
    /**
     * Get the tenant's unique identifier
     * @return string
     */
    public function getId(): string;

    /**
     * Get the tenant's name
     * @return string
     */
    public function getName(): string;

    /**
     * Get the tenant's database connection
     * @return string
     */
    public function getDatabaseConnection(): string;

    /**
     * Get the tenant's encryption key
     * @return string
     */
    public function getEncryptionKey(): string;

    /**
     * Get the tenant's administrators
     * @return array
     */
    public function getAdministrators(): array;

    /**
     * Get the tenant's billing information
     * @return array
     */
    public function getBillingInfo(): array;

    /**
     * Get the tenant's resource usage
     * @return array
     */
    public function getResourceUsage(): array;

    /**
     * Check if the tenant is active
     * @return bool
     */
    public function isActive(): bool;

    /**
     * Get the tenant's creation date
     * @return \DateTime
     */
    public function getCreatedAt(): \DateTime;

    /**
     * Get the tenant's last activity date
     * @return \DateTime
     */
    public function getLastActivity(): \DateTime;

    /**
     * Update the tenant's last activity
     * @return void
     */
    public function updateLastActivity(): void;

    /**
     * Get the tenant's audit log
     * @return array
     */
    public function getAuditLog(): array;

    /**
     * Add an entry to the tenant's audit log
     * @param string $action
     * @param array $details
     * @return void
     */
    public function logAuditEntry(string $action, array $details): void;
} 