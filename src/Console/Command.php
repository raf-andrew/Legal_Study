<?php

namespace LegalStudy\Console;

abstract class Command
{
    protected $name;
    protected $description;
    protected $arguments = [];
    protected $options = [];
    protected $help;

    public function __construct()
    {
        $this->configure();
    }

    abstract protected function configure(): void;

    abstract public function execute(array $input, array $output): int;

    public function getName(): string
    {
        return $this->name;
    }

    public function getDescription(): string
    {
        return $this->description;
    }

    public function getHelp(): string
    {
        return $this->help ?? $this->description;
    }

    public function getArguments(): array
    {
        return $this->arguments;
    }

    public function getOptions(): array
    {
        return $this->options;
    }

    protected function addArgument(string $name, string $description, bool $required = true): void
    {
        $this->arguments[$name] = [
            'description' => $description,
            'required' => $required
        ];
    }

    protected function addOption(string $name, string $description, bool $required = false, $default = null): void
    {
        $this->options[$name] = [
            'description' => $description,
            'required' => $required,
            'default' => $default
        ];
    }

    protected function validateInput(array $input): bool
    {
        foreach ($this->arguments as $name => $config) {
            if ($config['required'] && !isset($input[$name])) {
                return false;
            }
        }

        foreach ($this->options as $name => $config) {
            if ($config['required'] && !isset($input[$name])) {
                return false;
            }
        }

        return true;
    }
} 