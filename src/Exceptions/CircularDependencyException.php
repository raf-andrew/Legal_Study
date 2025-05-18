<?php

namespace LegalStudy\ModularInitialization\Exceptions;

class CircularDependencyException extends \RuntimeException
{
    private array $dependencyChain;

    public function __construct(array $dependencyChain)
    {
        $this->dependencyChain = $dependencyChain;
        parent::__construct(sprintf(
            'Circular dependency detected: %s',
            implode(' -> ', $dependencyChain)
        ));
    }

    public function getDependencyChain(): array
    {
        return $this->dependencyChain;
    }
} 