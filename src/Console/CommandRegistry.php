<?php

namespace LegalStudy\Console;

use LegalStudy\Console\Commands\CommandInterface;
use InvalidArgumentException;

class CommandRegistry
{
    /**
     * @var array<string, CommandInterface>
     */
    private array $commands = [];

    /**
     * Register a command
     *
     * @param CommandInterface $command
     * @return void
     */
    public function register(CommandInterface $command): void
    {
        $name = $command->getName();
        if (isset($this->commands[$name])) {
            throw new InvalidArgumentException("Command {$name} is already registered");
        }

        $this->commands[$name] = $command;
    }

    /**
     * Get a command by name
     *
     * @param string $name
     * @return CommandInterface
     */
    public function get(string $name): CommandInterface
    {
        if (!isset($this->commands[$name])) {
            throw new InvalidArgumentException("Command {$name} not found");
        }

        return $this->commands[$name];
    }

    /**
     * Check if a command exists
     *
     * @param string $name
     * @return bool
     */
    public function has(string $name): bool
    {
        return isset($this->commands[$name]);
    }

    /**
     * Get all commands
     *
     * @return array<string, CommandInterface>
     */
    public function all(): array
    {
        return $this->commands;
    }

    /**
     * Remove a command
     *
     * @param string $name
     * @return void
     */
    public function remove(string $name): void
    {
        if (!isset($this->commands[$name])) {
            throw new InvalidArgumentException("Command {$name} not found");
        }

        unset($this->commands[$name]);
    }

    /**
     * Clear all commands
     *
     * @return void
     */
    public function clear(): void
    {
        $this->commands = [];
    }

    public function getCommandHelp(string $name): ?string
    {
        return $this->has($name) ? $this->commands[$name]->getHelp() : null;
    }

    public function executeCommand(string $name, array $arguments): int
    {
        if (!$this->has($name)) {
            throw new \InvalidArgumentException("Command '{$name}' not found");
        }

        return $this->commands[$name]->execute($arguments);
    }

    public function getCommandNames(): array
    {
        return array_keys($this->commands);
    }

    public function getCommandDescriptions(): array
    {
        $descriptions = [];
        foreach ($this->commands as $name => $command) {
            $descriptions[$name] = $command->getDescription();
        }
        return $descriptions;
    }
} 