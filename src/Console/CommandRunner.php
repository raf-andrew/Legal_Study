<?php

namespace LegalStudy\Console;

class CommandRunner
{
    private $registry;
    private $input;
    private $output;

    public function __construct(CommandRegistry $registry)
    {
        $this->registry = $registry;
        $this->input = [];
        $this->output = [];
    }

    public function run(string $commandName, array $input = []): int
    {
        $command = $this->registry->getCommand($commandName);
        if (!$command) {
            $this->output[] = sprintf("Command '%s' not found.", $commandName);
            return 1;
        }

        $this->input = $input;
        return $command->execute($this->input, $this->output);
    }

    public function getOutput(): array
    {
        return $this->output;
    }

    public function clearOutput(): void
    {
        $this->output = [];
    }

    public function listCommands(): array
    {
        return $this->registry->getCommandDescriptions();
    }

    public function getCommandHelp(string $commandName): ?string
    {
        $command = $this->registry->getCommand($commandName);
        return $command ? $command->getHelp() : null;
    }
} 