<?php

namespace Mcp\Agent\Communication;

use Illuminate\Support\Facades\Log;
use Illuminate\Support\Facades\Cache;
use Illuminate\Support\Collection;
use Mcp\Agent\Agent;
use Mcp\Events\AgentMessageSent;
use Mcp\Events\AgentMessageReceived;
use Mcp\Events\AgentCommunicationError;

class AgentCommunicationManager
{
    protected string $cacheKey = 'mcp.agent.communication';
    protected int $cacheTTL = 3600; // 1 hour
    protected Collection $messageQueues;
    protected Collection $messageHistory;

    public function __construct()
    {
        $this->messageQueues = collect(Cache::get($this->cacheKey . '.queues', []));
        $this->messageHistory = collect(Cache::get($this->cacheKey . '.history', []));
    }

    public function sendMessage(Agent $sender, Agent $receiver, string $type, array $data = []): void
    {
        $message = new AgentMessage($sender->getId(), $receiver->getId(), $type, $data);
        
        if (!$this->messageQueues->has($receiver->getId())) {
            $this->messageQueues->put($receiver->getId(), collect());
        }
        
        $this->messageQueues->get($receiver->getId())->push($message);
        $this->messageHistory->push($message);
        
        $this->persistQueues();
        $this->persistHistory();
        
        event(new AgentMessageSent($sender, $receiver, $message));
        Log::info("Message sent from {$sender->getName()} to {$receiver->getName()}");
    }

    public function receiveMessage(Agent $receiver): ?AgentMessage
    {
        if (!$this->messageQueues->has($receiver->getId())) {
            return null;
        }
        
        $queue = $this->messageQueues->get($receiver->getId());
        if ($queue->isEmpty()) {
            return null;
        }
        
        $message = $queue->shift();
        $this->persistQueues();
        
        event(new AgentMessageReceived($receiver, $message));
        Log::info("Message received by {$receiver->getName()}");
        
        return $message;
    }

    public function getMessageHistory(Agent $agent, int $limit = 100): Collection
    {
        return $this->messageHistory
            ->filter(function (AgentMessage $message) use ($agent) {
                return $message->getSenderId() === $agent->getId() || 
                       $message->getReceiverId() === $agent->getId();
            })
            ->take($limit);
    }

    public function getMessageQueue(Agent $agent): Collection
    {
        return $this->messageQueues->get($agent->getId(), collect());
    }

    public function clearMessageQueue(Agent $agent): void
    {
        $this->messageQueues->forget($agent->getId());
        $this->persistQueues();
    }

    public function recordCommunicationError(Agent $agent, \Throwable $error): void
    {
        event(new AgentCommunicationError($agent, $error));
        Log::error("Communication error for agent {$agent->getName()}: {$error->getMessage()}");
    }

    protected function persistQueues(): void
    {
        $queuesArray = $this->messageQueues->map(function (Collection $queue) {
            return $queue->map(function (AgentMessage $message) {
                return $message->toArray();
            })->all();
        })->all();
        
        Cache::put($this->cacheKey . '.queues', $queuesArray, now()->addSeconds($this->cacheTTL));
    }

    protected function persistHistory(): void
    {
        $historyArray = $this->messageHistory->map(function (AgentMessage $message) {
            return $message->toArray();
        })->all();
        
        Cache::put($this->cacheKey . '.history', $historyArray, now()->addSeconds($this->cacheTTL));
    }
} 