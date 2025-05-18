<?php

namespace Mcp\Agent\Communication;

use Illuminate\Support\Collection;
use Illuminate\Support\Facades\Cache;
use Illuminate\Support\Facades\Log;
use Illuminate\Support\Facades\Event;

class MessageBus
{
    protected string $cacheKey = 'mcp.message_bus';
    protected int $cacheTTL = 3600; // 1 hour
    protected Collection $messages;
    protected Collection $subscribers;

    public function __construct()
    {
        $this->messages = collect(Cache::get($this->cacheKey . '.messages', []));
        $this->subscribers = collect(Cache::get($this->cacheKey . '.subscribers', []));
    }

    public function publish(AgentMessage $message): void
    {
        if ($message->isExpired()) {
            Log::warning("Attempted to publish expired message: {$message->getId()}");
            return;
        }

        $this->messages->put($message->getId(), $message);
        $this->persistMessages();

        Event::dispatch('mcp.message.published', [$message]);
        Log::info("Message published: {$message->getId()} of type {$message->getType()}");

        $this->notifySubscribers($message);
    }

    public function subscribe(string $agentId, array $messageTypes): void
    {
        $subscriptions = $this->subscribers->get($agentId, []);
        $subscriptions = array_unique(array_merge($subscriptions, $messageTypes));
        
        $this->subscribers->put($agentId, $subscriptions);
        $this->persistSubscribers();
        
        Log::info("Agent {$agentId} subscribed to message types: " . implode(', ', $messageTypes));
    }

    public function unsubscribe(string $agentId, ?array $messageTypes = null): void
    {
        if ($messageTypes === null) {
            $this->subscribers->forget($agentId);
        } else {
            $subscriptions = $this->subscribers->get($agentId, []);
            $subscriptions = array_diff($subscriptions, $messageTypes);
            
            if (empty($subscriptions)) {
                $this->subscribers->forget($agentId);
            } else {
                $this->subscribers->put($agentId, $subscriptions);
            }
        }
        
        $this->persistSubscribers();
        Log::info("Agent {$agentId} unsubscribed from message types");
    }

    public function getMessages(string $agentId): Collection
    {
        return $this->messages->filter(function (AgentMessage $message) use ($agentId) {
            if ($message->isExpired()) {
                return false;
            }

            if ($message->getReceiverId() === $agentId) {
                return true;
            }

            if ($message->getReceiverId() === null) {
                $subscribedTypes = $this->subscribers->get($agentId, []);
                return in_array($message->getType(), $subscribedTypes);
            }

            return false;
        });
    }

    public function acknowledgeMessage(string $messageId, string $agentId): void
    {
        $message = $this->messages->get($messageId);
        
        if ($message === null) {
            Log::warning("Attempted to acknowledge non-existent message: {$messageId}");
            return;
        }

        if ($message->getReceiverId() !== null && $message->getReceiverId() !== $agentId) {
            Log::warning("Agent {$agentId} attempted to acknowledge message {$messageId} intended for {$message->getReceiverId()}");
            return;
        }

        $this->messages->forget($messageId);
        $this->persistMessages();
        
        Log::info("Message {$messageId} acknowledged by agent {$agentId}");
    }

    public function clearExpiredMessages(): void
    {
        $expiredCount = 0;
        
        $this->messages = $this->messages->reject(function (AgentMessage $message) use (&$expiredCount) {
            if ($message->isExpired()) {
                $expiredCount++;
                return true;
            }
            return false;
        });
        
        if ($expiredCount > 0) {
            $this->persistMessages();
            Log::info("Cleared {$expiredCount} expired messages");
        }
    }

    protected function notifySubscribers(AgentMessage $message): void
    {
        if ($message->getReceiverId() !== null) {
            return;
        }

        $this->subscribers->each(function ($subscribedTypes, $agentId) use ($message) {
            if (in_array($message->getType(), $subscribedTypes)) {
                Event::dispatch('mcp.message.received', [$message, $agentId]);
                Log::info("Notified agent {$agentId} about message {$message->getId()}");
            }
        });
    }

    protected function persistMessages(): void
    {
        Cache::put(
            $this->cacheKey . '.messages',
            $this->messages->all(),
            now()->addSeconds($this->cacheTTL)
        );
    }

    protected function persistSubscribers(): void
    {
        Cache::put(
            $this->cacheKey . '.subscribers',
            $this->subscribers->all(),
            now()->addSeconds($this->cacheTTL)
        );
    }
} 