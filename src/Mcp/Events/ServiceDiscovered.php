<?php

namespace Mcp\Events;

use Illuminate\Queue\SerializesModels;
use Illuminate\Foundation\Events\Dispatchable;
use Illuminate\Broadcasting\InteractsWithSockets;

class ServiceDiscovered
{
    use Dispatchable, InteractsWithSockets, SerializesModels;

    /**
     * @var array
     */
    public $service;

    /**
     * Create a new event instance.
     *
     * @param array $service
     */
    public function __construct(array $service)
    {
        $this->service = $service;
    }
} 