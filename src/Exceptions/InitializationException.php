<?php

namespace LegalStudy\ModularInitialization\Exceptions;

use RuntimeException;

class InitializationException extends RuntimeException
{
    /**
     * @var array
     */
    protected array $context = [];

    /**
     * @param string $message
     * @param array $context
     * @param int $code
     * @param \Throwable|null $previous
     */
    public function __construct(string $message, array $context = [], int $code = 0, \Throwable $previous = null)
    {
        parent::__construct($message, $code, $previous);
        $this->context = $context;
    }

    /**
     * Get additional context information about the exception.
     *
     * @return array
     */
    public function getContext(): array
    {
        return $this->context;
    }
} 