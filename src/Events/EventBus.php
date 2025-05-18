<?php

namespace App\Events;

use Illuminate\Support\Collection;
use Illuminate\Support\Facades\Log;
use Illuminate\Contracts\Cache\Repository as Cache;

class EventBus
{
    private Collection $subscribers;
    private Collection $eventHistory;
    private Cache $cache;
    private int $maxHistorySize;

    public function __construct(Cache $cache, int $maxHistorySize = 1000)
    {
        $this->subscribers = new Collection();
        $this->eventHistory = new Collection();
        $this->cache = $cache;
        $this->maxHistorySize = $maxHistorySize;
    }

    public function publish(string $eventName, array $payload = []): void
    {
        $event = [
            'name' => $eventName,
            'payload' => $payload,
            'timestamp' => now(),
            'id' => uniqid('evt_', true)
        ];

        $this->recordEvent($event);

        if (!$this->subscribers->has($eventName)) {
            return;
        }

        foreach ($this->subscribers->get($eventName, []) as $subscriber) {
            try {
                $subscriber($event);
            } catch (\Throwable $e) {
                Log::error('Event subscriber error', [
                    'event' => $eventName,
                    'error' => $e->getMessage(),
                    'subscriber' => get_class($subscriber[0]) ?? 'closure'
                ]);
            }
        }
    }

    public function subscribe(string $eventName, callable $callback): string
    {
        $subscriberId = uniqid('sub_', true);

        if (!$this->subscribers->has($eventName)) {
            $this->subscribers->put($eventName, new Collection());
        }

        $this->subscribers->get($eventName)->put($subscriberId, $callback);

        return $subscriberId;
    }

    public function unsubscribe(string $eventName, string $subscriberId): bool
    {
        if (!$this->subscribers->has($eventName)) {
            return false;
        }

        $subscribers = $this->subscribers->get($eventName);
        if (!$subscribers->has($subscriberId)) {
            return false;
        }

        $subscribers->forget($subscriberId);
        if ($subscribers->isEmpty()) {
            $this->subscribers->forget($eventName);
        }

        return true;
    }

    private function recordEvent(array $event): void
    {
        $this->eventHistory->prepend($event);
        
        if ($this->eventHistory->count() > $this->maxHistorySize) {
            $this->eventHistory->pop();
        }

        // Cache the event for persistence
        $cacheKey = "event_history:{$event['id']}";
        $this->cache->put($cacheKey, $event, now()->addDays(7));
    }

    public function getEventHistory(?string $eventName = null, ?int $limit = null): Collection
    {
        if (!$eventName) {
            return $limit ? $this->eventHistory->take($limit) : $this->eventHistory;
        }

        $filtered = $this->eventHistory->filter(function ($event) use ($eventName) {
            return $event['name'] === $eventName;
        });

        return $limit ? $filtered->take($limit) : $filtered;
    }

    public function clearEventHistory(): void
    {
        $this->eventHistory = new Collection();
    }

    public function getSubscriberCount(string $eventName): int
    {
        return $this->subscribers->get($eventName, new Collection())->count();
    }

    public function getAllEventTypes(): array
    {
        return $this->subscribers->keys()->all();
    }
} 