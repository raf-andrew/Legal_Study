<?php

namespace App\Mcp\Core\EventBus;

use Illuminate\Support\Facades\Log;

class EventBus implements EventBusInterface
{
    protected array $handlers = [];
    protected array $priorities = [];

    public function registerHandler(string $eventType, callable $handler, int $priority = 0): bool
    {
        if (!isset($this->handlers[$eventType])) {
            $this->handlers[$eventType] = [];
            $this->priorities[$eventType] = [];
        }

        // Check if handler is already registered
        if (in_array($handler, $this->handlers[$eventType], true)) {
            Log::warning("Handler already registered for event type: {$eventType}");
            return false;
        }

        $this->handlers[$eventType][] = $handler;
        $this->priorities[$eventType][] = $priority;

        // Sort handlers by priority
        array_multisort($this->priorities[$eventType], SORT_DESC, $this->handlers[$eventType]);

        Log::info("Handler registered for event type: {$eventType} with priority: {$priority}");
        return true;
    }

    public function unregisterHandler(string $eventType, callable $handler): bool
    {
        if (!isset($this->handlers[$eventType])) {
            Log::warning("No handlers registered for event type: {$eventType}");
            return false;
        }

        $index = array_search($handler, $this->handlers[$eventType], true);
        if ($index === false) {
            Log::warning("Handler not found for event type: {$eventType}");
            return false;
        }

        unset($this->handlers[$eventType][$index], $this->priorities[$eventType][$index]);
        
        // Reindex arrays
        $this->handlers[$eventType] = array_values($this->handlers[$eventType]);
        $this->priorities[$eventType] = array_values($this->priorities[$eventType]);

        Log::info("Handler unregistered for event type: {$eventType}");
        return true;
    }

    public function dispatch(string $eventType, mixed $eventData): array
    {
        if (!isset($this->handlers[$eventType])) {
            Log::info("No handlers registered for event type: {$eventType}");
            return [];
        }

        $results = [];
        foreach ($this->handlers[$eventType] as $handler) {
            try {
                $result = $handler($eventData);
                $results[] = $result;
            } catch (\Throwable $e) {
                Log::error("Error in event handler for {$eventType}: " . $e->getMessage());
                $results[] = null;
            }
        }

        return $results;
    }

    public function getHandlers(string $eventType): array
    {
        return $this->handlers[$eventType] ?? [];
    }

    public function clearHandlers(string $eventType): bool
    {
        if (!isset($this->handlers[$eventType])) {
            return false;
        }

        unset($this->handlers[$eventType], $this->priorities[$eventType]);
        Log::info("Handlers cleared for event type: {$eventType}");
        return true;
    }

    public function hasHandlers(string $eventType): bool
    {
        return isset($this->handlers[$eventType]) && !empty($this->handlers[$eventType]);
    }
} 