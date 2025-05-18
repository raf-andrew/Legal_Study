<?php

namespace Mcp\Console\Shell;

use Illuminate\Console\Command;
use Illuminate\Support\Facades\Artisan;
use Illuminate\Support\Str;
use Symfony\Component\Console\Input\InputInterface;
use Symfony\Component\Console\Output\OutputInterface;
use Symfony\Component\Console\Question\Question;

class McpShell extends Command
{
    protected $signature = 'mcp:shell';
    protected $description = 'Start an interactive MCP shell';

    protected array $history = [];
    protected array $customCommands = [];
    protected array $aliases = [];
    protected string $prompt = 'mcp> ';

    public function __construct()
    {
        parent::__construct();

        $this->registerCustomCommands();
        $this->registerAliases();
    }

    protected function execute(InputInterface $input, OutputInterface $output)
    {
        $this->info('Welcome to the MCP Interactive Shell');
        $this->info('Type "help" for a list of commands, "exit" to quit');
        $this->info('');

        while (true) {
            $command = $this->askQuestion();

            if (empty($command)) {
                continue;
            }

            if ($command === 'exit') {
                break;
            }

            $this->processCommand($command);
            $this->history[] = $command;
        }

        return 0;
    }

    protected function askQuestion(): string
    {
        $question = new Question($this->prompt);
        
        $question->setAutocompleterValues($this->getAutocompleteValues());
        
        return trim($this->ask($question));
    }

    protected function processCommand(string $command): void
    {
        if ($command === 'help') {
            $this->showHelp();
            return;
        }

        if ($command === 'history') {
            $this->showHistory();
            return;
        }

        if (Str::startsWith($command, 'alias ')) {
            $this->defineAlias(substr($command, 6));
            return;
        }

        if (array_key_exists($command, $this->aliases)) {
            $command = $this->aliases[$command];
        }

        if (array_key_exists($command, $this->customCommands)) {
            $this->customCommands[$command]();
            return;
        }

        try {
            Artisan::call($command, [], $this->output);
        } catch (\Exception $e) {
            $this->error("Error executing command: {$e->getMessage()}");
        }
    }

    protected function showHelp(): void
    {
        $this->info('Available Commands:');
        $this->info('');
        
        // Built-in commands
        $this->info('Built-in Commands:');
        $this->line('  help     - Show this help message');
        $this->line('  exit     - Exit the shell');
        $this->line('  history  - Show command history');
        $this->line('  alias    - Define command alias (e.g., alias ll=list)');
        $this->info('');
        
        // Custom commands
        $this->info('Custom Commands:');
        foreach ($this->customCommands as $name => $callback) {
            $this->line("  $name");
        }
        $this->info('');
        
        // Aliases
        $this->info('Defined Aliases:');
        foreach ($this->aliases as $alias => $command) {
            $this->line("  $alias -> $command");
        }
        $this->info('');
        
        // Artisan commands
        $this->info('Available Artisan Commands:');
        $commands = collect(Artisan::all())->sortBy(function ($command, $name) {
            return $name;
        });
        
        foreach ($commands as $name => $command) {
            $this->line("  $name - {$command->getDescription()}");
        }
    }

    protected function showHistory(): void
    {
        $this->info('Command History:');
        foreach ($this->history as $index => $command) {
            $this->line(sprintf(' %d  %s', $index + 1, $command));
        }
    }

    protected function defineAlias(string $definition): void
    {
        $parts = explode('=', $definition, 2);
        if (count($parts) !== 2) {
            $this->error('Invalid alias definition. Format: alias name=command');
            return;
        }

        $alias = trim($parts[0]);
        $command = trim($parts[1]);

        $this->aliases[$alias] = $command;
        $this->info("Alias defined: $alias -> $command");
    }

    protected function getAutocompleteValues(): array
    {
        return array_merge(
            ['help', 'exit', 'history', 'alias'],
            array_keys($this->customCommands),
            array_keys($this->aliases),
            array_keys(Artisan::all())
        );
    }

    protected function registerCustomCommands(): void
    {
        $this->customCommands = [
            'agents' => function () {
                $this->call('mcp:agents');
            },
            'tasks' => function () {
                $this->call('mcp:tasks');
            },
            'discover' => function () {
                $this->call('mcp:discover');
            },
            'monitor' => function () {
                $this->call('mcp:monitor');
            },
            'status' => function () {
                $this->call('mcp:status');
            },
            'clear' => function () {
                $this->output->write("\033[H\033[2J");
            }
        ];
    }

    protected function registerAliases(): void
    {
        $this->aliases = [
            'll' => 'list',
            'ps' => 'status',
            'cls' => 'clear'
        ];
    }
} 