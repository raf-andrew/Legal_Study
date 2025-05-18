<?php

namespace App\Mcp\Service;

use App\Mcp\ConfigurationManager;
use App\Mcp\EventBus;
use Illuminate\Support\Facades\Log;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Collection;

class Actuator
{
    protected $config;
    protected $eventBus;
    protected $discovery;

    public function __construct(ConfigurationManager $config, EventBus $eventBus, Discovery $discovery)
    {
        $this->config = $config;
        $this->eventBus = $eventBus;
        $this->discovery = $discovery;
    }

    public function executeAction($serviceName, $action, array $parameters = [])
    {
        $service = $this->discovery->getService($serviceName);
        
        if (!$service) {
            throw new \Exception("Service not found: {$serviceName}");
        }

        switch ($service['type']) {
            case 'api_endpoint':
                return $this->executeApiAction($service, $action, $parameters);
            case 'service_provider':
                return $this->executeServiceAction($service, $action, $parameters);
            case 'event_listener':
                return $this->executeEventAction($service, $action, $parameters);
            default:
                throw new \Exception("Unsupported service type: {$service['type']}");
        }
    }

    protected function executeApiAction($service, $action, array $parameters)
    {
        $method = strtoupper($action);
        $url = url($service['name']);

        if (!in_array($method, $service['metadata']['methods'])) {
            throw new \Exception("Method {$method} not supported for endpoint {$service['name']}");
        }

        try {
            $response = Http::withHeaders([
                'X-MCP-Action' => 'true',
            ])->$action($url, $parameters);

            if ($response->successful()) {
                $this->logAction($service, $action, true);
                return $response->json();
            }

            throw new \Exception("API request failed: " . $response->status());
        } catch (\Exception $e) {
            $this->logAction($service, $action, false, $e->getMessage());
            throw $e;
        }
    }

    protected function executeServiceAction($service, $action, array $parameters)
    {
        $serviceClass = $service['name'];
        $serviceInstance = app($serviceClass);

        if (!method_exists($serviceInstance, $action)) {
            throw new \Exception("Action {$action} not supported for service {$serviceClass}");
        }

        try {
            $result = $serviceInstance->$action(...array_values($parameters));
            $this->logAction($service, $action, true);
            return $result;
        } catch (\Exception $e) {
            $this->logAction($service, $action, false, $e->getMessage());
            throw $e;
        }
    }

    protected function executeEventAction($service, $action, array $parameters)
    {
        if ($action !== 'trigger') {
            throw new \Exception("Only 'trigger' action is supported for event listeners");
        }

        $event = $service['metadata']['event'];

        try {
            event($event, $parameters);
            $this->logAction($service, $action, true);
            return true;
        } catch (\Exception $e) {
            $this->logAction($service, $action, false, $e->getMessage());
            throw $e;
        }
    }

    protected function logAction($service, $action, $success, $error = null)
    {
        $data = [
            'service' => $service['name'],
            'type' => $service['type'],
            'action' => $action,
            'success' => $success,
            'timestamp' => now(),
        ];

        if ($error) {
            $data['error'] = $error;
        }

        $this->eventBus->publish('service.action', $data);

        if ($success) {
            Log::info("Service action executed successfully", $data);
        } else {
            Log::error("Service action failed", $data);
        }
    }

    public function getAvailableActions($serviceName)
    {
        $service = $this->discovery->getService($serviceName);
        
        if (!$service) {
            throw new \Exception("Service not found: {$serviceName}");
        }

        switch ($service['type']) {
            case 'api_endpoint':
                return $service['metadata']['methods'];
            case 'service_provider':
                return $this->getServiceMethods($service['name']);
            case 'event_listener':
                return ['trigger'];
            default:
                return [];
        }
    }

    protected function getServiceMethods($serviceClass)
    {
        $methods = get_class_methods($serviceClass);
        return array_filter($methods, function ($method) {
            return !in_array($method, ['__construct', '__destruct']) && 
                   strpos($method, '__') !== 0;
        });
    }
} 