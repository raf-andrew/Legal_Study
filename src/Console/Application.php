<?php

namespace LegalStudy\Console;

use Symfony\Component\Console\Application as SymfonyApplication;
use LegalStudy\Console\Commands\CommandInterface;
use Symfony\Component\Console\Input\InputInterface;
use Symfony\Component\Console\Output\OutputInterface;

class Application extends SymfonyApplication
{
    /**
     * @var CommandRegistry
     */
    private CommandRegistry $registry;

    /**
     * @param array $config
     */
    public function __construct(array $config = [])
    {
        parent::__construct(
            $config['name'] ?? 'Legal Study System',
            $config['version'] ?? '1.0.0'
        );

        $this->registry = new CommandRegistry();
    }

    /**
     * Register a command
     *
     * @param CommandInterface $command
     * @return void
     */
    public function registerCommand(CommandInterface $command): void
    {
        $this->registry->register($command);
        $this->add($command);
    }

    /**
     * Get command registry
     *
     * @return CommandRegistry
     */
    public function getRegistry(): CommandRegistry
    {
        return $this->registry;
    }

    /**
     * Run the application
     *
     * @param InputInterface|null $input
     * @param OutputInterface|null $output
     * @return int
     */
    public function run(?InputInterface $input = null, ?OutputInterface $output = null): int
    {
        try {
            return parent::run($input, $output);
        } catch (\Exception $e) {
            if ($output) {
                $this->renderException($e, $output);
            }
            return 1;
        }
    }
} 