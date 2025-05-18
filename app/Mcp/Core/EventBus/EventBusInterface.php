<?php

namespace App\Mcp\Core\EventBus;

interface EventBusInterface
{
    /**
     * Register an event handler for a specific event type.
     *
     * @param string $eventType The type of event to handle
     * @param callable $handler The handler function to call when the event occurs
     * @param int $priority The priority of the handler (higher numbers are called first)
     * @return bool True if the handler was registered successfully
     */
    public function registerHandler(string $eventType, callable $handler, int $priority = 0): bool;

    /**
     * Unregister an event handler for a specific event type.
     *
     * @param string $eventType The type of event
     * @param callable $handler The handler function to unregister
     * @return bool True if the handler was unregistered successfully
     */
    public function unregisterHandler(string $eventType, callable $handler): bool;

    /**
     * Dispatch an event to all registered handlers.
     *
     * @param string $eventType The type of event to dispatch
     * @param mixed $eventData The data associated with the event
     * @return array The results from all handlers
     */
    public function dispatch(string $eventType, mixed $eventData): array;

    /**
     * Get all registered handlers for a specific event type.
     *
     * @param string $eventType The type of event
     * @return array The registered handlers
     */
    public function getHandlers(string $eventType): array;

    /**
     * Clear all handlers for a specific event type.
     *
     * @param string $eventType The type of event
     * @return bool True if the handlers were cleared successfully
     */
    public function clearHandlers(string $eventType): bool;

    /**
     * Check if there are any handlers registered for a specific event type.
     *
     * @param string $eventType The type of event
     * @return bool True if there are handlers registered
     */
    public function hasHandlers(string $eventType): bool;
} 