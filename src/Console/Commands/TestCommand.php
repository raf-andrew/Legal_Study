<?php

namespace LegalStudy\Console\Commands;

use Symfony\Component\Console\Input\InputInterface;
use Symfony\Component\Console\Output\OutputInterface;

class TestCommand extends AbstractCommand
{
    /**
     * @var string
     */
    protected string $name = 'test:run';

    /**
     * @var string
     */
    protected string $description = 'Run application tests';

    /**
     * @var string
     */
    protected string $help = 'This is a test command to demonstrate the command infrastructure.';

    /**
     * @var array
     */
    protected array $arguments = [
        [
            'name' => 'message',
            'description' => 'The message to display',
            'mode' => InputArgument::OPTIONAL,
            'default' => 'Hello, World!'
        ]
    ];

    /**
     * @var array
     */
    protected array $options = [
        'filter' => [
            'shortcut' => 'f',
            'mode' => null,
            'description' => 'Filter tests to run',
            'default' => null
        ],
        'verbose' => [
            'shortcut' => 'v',
            'mode' => null,
            'description' => 'Show detailed test output',
            'default' => false
        ]
    ];

    /**
     * Handle the command execution
     *
     * @param InputInterface $input
     * @param OutputInterface $output
     * @return int
     */
    protected function handle(InputInterface $input, OutputInterface $output): int
    {
        $message = $input->getArgument('message');
        if ($input->getOption('uppercase')) {
            $message = strtoupper($message);
        }

        $output->writeln($message);
        return Command::SUCCESS;
    }

    protected function configureCommand(): void
    {
        $this->options = [
            'filter' => [
                'shortcut' => 'f',
                'mode' => null,
                'description' => 'Filter tests to run',
                'default' => null
            ],
            'verbose' => [
                'shortcut' => 'v',
                'mode' => null,
                'description' => 'Show detailed test output',
                'default' => false
            ]
        ];
    }

    protected function executeCommand(InputInterface $input, OutputInterface $output): int
    {
        $output->writeln('<info>Running tests...</info>');

        $filter = $input->getOption('filter');
        $verbose = $input->getOption('verbose');

        // Simulate running tests
        $testResults = $this->runTests($filter);

        if ($verbose) {
            foreach ($testResults as $test => $result) {
                $output->writeln(sprintf(
                    '<%s>%s: %s</%s>',
                    $result['passed'] ? 'info' : 'error',
                    $test,
                    $result['message'],
                    $result['passed'] ? 'info' : 'error'
                ));
            }
        }

        $failedTests = array_filter($testResults, fn($result) => !$result['passed']);
        
        if (empty($failedTests)) {
            $output->writeln('<info>All tests passed successfully.</info>');
            return self::SUCCESS;
        }

        $output->writeln(sprintf(
            '<error>%d test(s) failed. Run with -v for details.</error>',
            count($failedTests)
        ));
        return self::FAILURE;
    }

    private function runTests(?string $filter): array
    {
        // Simulate test execution
        return [
            'TestCase1' => [
                'passed' => true,
                'message' => 'Test passed'
            ],
            'TestCase2' => [
                'passed' => true,
                'message' => 'Test passed'
            ]
        ];
    }
} 