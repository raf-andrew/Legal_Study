<?php

namespace App\Mcp;

use Illuminate\Support\Collection;
use Illuminate\Support\Facades\Log;

class EventBus
{
    protected $subscribers = [];
    protected $events = [];

    public function subscribe(string $event, callable $callback): void
    {
        if (!isset($this->subscribers[$event])) {
            $this->subscribers[$event] = new Collection();
        }

        $this->subscribers[$event]->push($callback);
        Log::debug("MCP EventBus: Subscriber added for event {$event}");
    }

    public function unsubscribe(string $event, callable $callback): void
    {
        if (!isset($this->subscribers[$event])) {
            return;
        }

        $this->subscribers[$event] = $this->subscribers[$event]->reject(function ($subscriber) use ($callback) {
            return $subscriber === $callback;
        });

        Log::debug("MCP EventBus: Subscriber removed from event {$event}");
    }

    public function publish(string $event, array $data = []): void
    {
        if (!isset($this->subscribers[$event])) {
            Log::debug("MCP EventBus: No subscribers for event {$event}");
            return;
        }

        $this->events[] = [
            'event' => $event,
            'data' => $data,
            'timestamp' => now(),
        ];

        $this->subscribers[$event]->each(function ($subscriber) use ($event, $data) {
            try {
                $subscriber($data);
            } catch (\Exception $e) {
                Log::error("MCP EventBus: Error processing event {$event}: " . $e->getMessage());
            }
        });

        Log::debug("MCP EventBus: Event {$event} published");
    }

    public function getEvents(string $event = null): array
    {
        if ($event === null) {
            return $this->events;
        }

        return array_filter($this->events, function ($e) use ($event) {
            return $e['event'] === $event;
        });
    }

    public function clearEvents(): void
    {
        $this->events = [];
        Log::debug("MCP EventBus: Event history cleared");
    }

    public function getSubscribers(string $event = null): Collection
    {
        if ($event === null) {
            return new Collection($this->subscribers);
        }

        return $this->subscribers[$event] ?? new Collection();
    }
} 