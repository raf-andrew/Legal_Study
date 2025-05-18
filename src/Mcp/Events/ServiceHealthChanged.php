<?php

namespace Mcp\Events;

use Illuminate\Queue\SerializesModels;
use Illuminate\Foundation\Events\Dispatchable;
use Illuminate\Broadcasting\InteractsWithSockets;

class ServiceHealthChanged
{
    use Dispatchable, InteractsWithSockets, SerializesModels;

    /**
     * @var string
     */
    public $serviceClass;

    /**
     * @var string
     */
    public $method;

    /**
     * @var array
     */
    public $metrics;

    /**
     * Create a new event instance.
     *
     * @param string $serviceClass
     * @param string $method
     * @param array $metrics
     */
    public function __construct(string $serviceClass, string $method, array $metrics)
    {
        $this->serviceClass = $serviceClass;
        $this->method = $method;
        $this->metrics = $metrics;
    }
} 