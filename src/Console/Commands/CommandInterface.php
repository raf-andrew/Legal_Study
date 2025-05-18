<?php

namespace LegalStudy\Console\Commands;

use Symfony\Component\Console\Input\InputInterface;
use Symfony\Component\Console\Output\OutputInterface;

interface CommandInterface
{
    /**
     * Configure the command
     */
    public function configure(): void;

    /**
     * Execute the command
     *
     * @param InputInterface $input
     * @param OutputInterface $output
     * @return int
     */
    public function execute(InputInterface $input, OutputInterface $output): int;

    /**
     * Get the command name
     *
     * @return string
     */
    public function getName(): string;

    /**
     * Get the command description
     *
     * @return string
     */
    public function getDescription(): string;

    /**
     * Get the command help text
     *
     * @return string
     */
    public function getHelp(): string;

    /**
     * Get the command aliases
     *
     * @return array
     */
    public function getAliases(): array;

    /**
     * Get command arguments
     *
     * @return array
     */
    public function getArguments(): array;

    /**
     * Get command options
     *
     * @return array
     */
    public function getOptions(): array;

    /**
     * Validate command arguments
     *
     * @param array $arguments
     * @return bool
     */
    public function validateArguments(array $arguments): bool;
} 