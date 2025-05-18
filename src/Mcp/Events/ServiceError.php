<?php

namespace Mcp\Events;

use Illuminate\Queue\SerializesModels;
use Illuminate\Foundation\Events\Dispatchable;
use Illuminate\Broadcasting\InteractsWithSockets;

class ServiceError
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
     * @var \Throwable
     */
    public $error;

    /**
     * Create a new event instance.
     *
     * @param string $serviceClass
     * @param string $method
     * @param \Throwable $error
     */
    public function __construct(string $serviceClass, string $method, \Throwable $error)
    {
        $this->serviceClass = $serviceClass;
        $this->method = $method;
        $this->error = $error;
    }
} 