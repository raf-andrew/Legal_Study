<?php

namespace App\Console\Commands;

use Illuminate\Console\Command;
use App\Services\CodespacesServiceManager;
use App\Services\CodespacesHealthCheck;
use App\Services\CodespacesLifecycleManager;

class ManageCodespaces extends Command
{
    protected $signature = 'codespaces:manage
        {action : The action to perform (enable|disable|check|rebuild|create|teardown|heal|status)}
        {service? : The service to manage}';

    protected $description = 'Manage Codespaces services';

    protected $serviceManager;
    protected $healthCheck;
    protected $lifecycleManager;

    public function __construct(
        CodespacesServiceManager $serviceManager,
        CodespacesHealthCheck $healthCheck,
        CodespacesLifecycleManager $lifecycleManager
    ) {
        parent::__construct();
        $this->serviceManager = $serviceManager;
        $this->healthCheck = $healthCheck;
        $this->lifecycleManager = $lifecycleManager;
    }

    public function handle()
    {
        $action = $this->argument('action');
        $service = $this->argument('service');

        if ($service && !in_array($service, ['mysql', 'redis'])) {
            $this->error("Invalid service: {$service}");
            return 1;
        }

        return match ($action) {
            'enable' => $this->handleEnable($service),
            'disable' => $this->handleDisable($service),
            'check' => $this->handleCheck($service),
            'rebuild' => $this->handleRebuild($service),
            'create' => $this->handleCreate($service),
            'teardown' => $this->handleTeardown($service),
            'heal' => $this->handleHeal($service),
            'status' => $this->handleStatus($service),
            default => $this->handleInvalidAction($action),
        };
    }

    protected function handleEnable(?string $service): int
    {
        if ($service) {
            return $this->enableService($service);
        }

        $this->info('Enabling all services...');
        $success = true;
        foreach (['mysql', 'redis'] as $service) {
            if (!$this->enableService($service)) {
                $success = false;
            }
        }
        return $success ? 0 : 1;
    }

    protected function handleDisable(?string $service): int
    {
        if ($service) {
            return $this->disableService($service);
        }

        $this->info('Disabling all services...');
        $success = true;
        foreach (['mysql', 'redis'] as $service) {
            if (!$this->disableService($service)) {
                $success = false;
            }
        }
        return $success ? 0 : 1;
    }

    protected function handleCheck(?string $service): int
    {
        if ($service) {
            return $this->checkService($service);
        }

        $this->info('Checking all services...');
        $success = true;
        foreach (['mysql', 'redis'] as $service) {
            if (!$this->checkService($service)) {
                $success = false;
            }
        }
        return $success ? 0 : 1;
    }

    protected function handleRebuild(?string $service): int
    {
        if ($service) {
            return $this->rebuildService($service);
        }

        $this->info('Rebuilding all services...');
        $success = true;
        foreach (['mysql', 'redis'] as $service) {
            if (!$this->rebuildService($service)) {
                $success = false;
            }
        }
        return $success ? 0 : 1;
    }

    protected function handleCreate(?string $service): int
    {
        if ($service) {
            return $this->createService($service);
        }

        $this->info('Creating all services...');
        $success = true;
        foreach (['mysql', 'redis'] as $service) {
            if (!$this->createService($service)) {
                $success = false;
            }
        }
        return $success ? 0 : 1;
    }

    protected function handleTeardown(?string $service): int
    {
        if ($service) {
            return $this->teardownService($service);
        }

        $this->info('Tearing down all services...');
        $success = true;
        foreach (['mysql', 'redis'] as $service) {
            if (!$this->teardownService($service)) {
                $success = false;
            }
        }
        return $success ? 0 : 1;
    }

    protected function handleHeal(?string $service): int
    {
        if ($service) {
            return $this->healService($service);
        }

        $this->info('Healing all services...');
        $success = true;
        foreach (['mysql', 'redis'] as $service) {
            if (!$this->healService($service)) {
                $success = false;
            }
        }
        return $success ? 0 : 1;
    }

    protected function handleStatus(?string $service): int
    {
        if ($service) {
            return $this->showServiceStatus($service);
        }

        $this->info('Service Status:');
        foreach (['mysql', 'redis'] as $service) {
            $this->showServiceStatus($service);
        }
        return 0;
    }

    protected function handleInvalidAction(string $action): int
    {
        $this->error("Invalid action: {$action}");
        $this->info('Available actions: enable, disable, check, rebuild, create, teardown, heal, status');
        return 1;
    }

    protected function enableService(string $service): int
    {
        $this->info("Enabling {$service}...");
        if ($this->serviceManager->enableService($service)) {
            $this->info("{$service} enabled successfully");
            return 0;
        }
        $this->error("Failed to enable {$service}");
        return 1;
    }

    protected function disableService(string $service): int
    {
        $this->info("Disabling {$service}...");
        if ($this->serviceManager->disableService($service)) {
            $this->info("{$service} disabled successfully");
            return 0;
        }
        $this->error("Failed to disable {$service}");
        return 1;
    }

    protected function checkService(string $service): int
    {
        $this->info("Checking {$service}...");
        if ($this->healthCheck->checkService($service)) {
            $this->info("{$service} is healthy");
            return 0;
        }
        $this->error("{$service} is unhealthy");
        return 1;
    }

    protected function rebuildService(string $service): int
    {
        $this->info("Rebuilding {$service}...");
        if ($this->healthCheck->rebuildService($service)) {
            $this->info("{$service} rebuilt successfully");
            return 0;
        }
        $this->error("Failed to rebuild {$service}");
        return 1;
    }

    protected function createService(string $service): int
    {
        $this->info("Creating {$service} service...");
        if ($this->lifecycleManager->createService($service)) {
            $this->info("{$service} service created successfully");
            return 0;
        }
        $this->error("Failed to create {$service} service");
        return 1;
    }

    protected function teardownService(string $service): int
    {
        $this->info("Tearing down {$service} service...");
        if ($this->lifecycleManager->teardownService($service)) {
            $this->info("{$service} service torn down successfully");
            return 0;
        }
        $this->error("Failed to tear down {$service} service");
        return 1;
    }

    protected function healService(string $service): int
    {
        $this->info("Healing {$service} service...");
        if ($this->lifecycleManager->healService($service)) {
            $this->info("{$service} service healed successfully");
            return 0;
        }
        $this->error("Failed to heal {$service} service");
        return 1;
    }

    protected function showServiceStatus(string $service): int
    {
        $state = $this->lifecycleManager->getServiceState($service);
        $enabled = $this->serviceManager->isServiceEnabled($service);
        $healthy = $this->healthCheck->checkService($service);

        $this->info("\n{$service}:");
        $this->info("  Enabled: " . ($enabled ? 'Yes' : 'No'));
        $this->info("  Status: " . ($state['status'] ?? 'unknown'));
        $this->info("  Health: " . ($healthy ? 'Healthy' : 'Unhealthy'));

        if ($state) {
            $this->info("  Created: " . ($state['created_at'] ?? 'N/A'));
            $this->info("  Last Health Check: " . ($state['last_health_check'] ?? 'N/A'));
        }

        return 0;
    }
}
