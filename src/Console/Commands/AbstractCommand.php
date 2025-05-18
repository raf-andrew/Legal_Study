<?php

namespace LegalStudy\Console\Commands;

use Symfony\Component\Console\Command\Command;
use Symfony\Component\Console\Input\InputInterface;
use Symfony\Component\Console\Output\OutputInterface;
use Symfony\Component\Console\Input\InputArgument;
use Symfony\Component\Console\Input\InputOption;

abstract class AbstractCommand extends Command implements CommandInterface
{
    /**
     * @var string
     */
    protected string $name;

    /**
     * @var string
     */
    protected string $description;

    /**
     * @var array
     */
    protected array $arguments = [];

    /**
     * @var array
     */
    protected array $options = [];

    /**
     * @var array
     */
    protected array $aliases = [];

    /**
     * AbstractCommand constructor.
     */
    public function __construct()
    {
        parent::__construct($this->name);
        $this->setDescription($this->description);
        $this->configureCommand();
    }

    /**
     * Configure the command
     */
    abstract protected function configureCommand(): void;

    /**
     * Execute the command
     *
     * @param InputInterface $input
     * @param OutputInterface $output
     * @return int
     */
    abstract protected function executeCommand(InputInterface $input, OutputInterface $output): int;

    /**
     * {@inheritdoc}
     */
    public function configure(): void
    {
        $this->setName($this->getName())
            ->setDescription($this->getDescription())
            ->setHelp($this->getHelp())
            ->setAliases($this->getAliases());

        foreach ($this->arguments as $name => $config) {
            $this->addArgument(
                $name,
                $config['mode'] ?? null,
                $config['description'] ?? '',
                $config['default'] ?? null
            );
        }

        foreach ($this->options as $name => $config) {
            $this->addOption(
                $name,
                $config['shortcut'] ?? null,
                $config['mode'] ?? null,
                $config['description'] ?? '',
                $config['default'] ?? null
            );
        }
    }

    /**
     * {@inheritdoc}
     */
    public function execute(InputInterface $input, OutputInterface $output): int
    {
        return $this->executeCommand($input, $output);
    }

    /**
     * Initialize the command
     *
     * @param InputInterface $input
     * @param OutputInterface $output
     * @return void
     */
    protected function initialize(InputInterface $input, OutputInterface $output): void
    {
        // Override this method in child classes if needed
    }

    /**
     * Get command arguments
     *
     * @return array
     */
    public function getArguments(): array
    {
        return $this->arguments;
    }

    /**
     * Get command options
     *
     * @return array
     */
    public function getOptions(): array
    {
        return $this->options;
    }

    /**
     * Get command aliases
     *
     * @return array
     */
    public function getAliases(): array
    {
        return $this->aliases;
    }

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
        $help = "Command: {$this->name}\n";
        $help .= "Description: {$this->description}\n\n";
        
        if (!empty($this->arguments)) {
            $help .= "Arguments:\n";
            foreach ($this->arguments as $name => $config) {
                $help .= "  {$name}: {$config['description']}\n";
            }
        }

        if (!empty($this->options)) {
            $help .= "\nOptions:\n";
            foreach ($this->options as $name => $config) {
                $help .= "  {$name}: {$config['description']}\n";
            }
        }

        return $help;
    }

    public function validateArguments(array $arguments): bool
    {
        foreach ($this->arguments as $name => $config) {
            if (!isset($arguments[$name])) {
                return false;
            }
        }
        return true;
    }

    /**
     * Format error message
     *
     * @param string $message
     * @return string
     */
    protected function formatError(string $message): string
    {
        return "\033[31mError: {$message}\033[0m";
    }

    /**
     * Format success message
     *
     * @param string $message
     * @return string
     */
    protected function formatSuccess(string $message): string
    {
        return "\033[32mSuccess: {$message}\033[0m";
    }

    /**
     * Format warning message
     *
     * @param string $message
     * @return string
     */
    protected function formatWarning(string $message): string
    {
        return "\033[33mWarning: {$message}\033[0m";
    }
} 