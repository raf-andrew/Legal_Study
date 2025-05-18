<?php

namespace Mcp\Console\Commands;

use Illuminate\Console\Command;
use Mcp\Console\Generator\CodeGenerator;
use Illuminate\Support\Str;

class McpGenerate extends Command
{
    protected $signature = 'mcp:generate
                          {type : The type of class to generate (command, controller, model, service, event, listener, policy)}
                          {name : The name of the class}
                          {--namespace= : The namespace for the class}
                          {--test : Generate a test class}
                          {--force : Overwrite existing files}';

    protected $description = 'Generate a new class and its test';

    protected CodeGenerator $generator;

    public function __construct(CodeGenerator $generator)
    {
        parent::__construct();
        $this->generator = $generator;
    }

    public function handle(): int
    {
        $type = $this->argument('type');
        $name = $this->argument('name');
        $namespace = $this->getNamespace();
        $generateTest = $this->option('test');

        try {
            // Generate the class
            $classPath = $this->generator->generateClass(
                $type,
                $name,
                $namespace,
                $this->getOptions($type)
            );

            $this->info("Generated {$type} class at: {$classPath}");

            // Generate the test if requested
            if ($generateTest) {
                $testPath = $this->generator->generateTest(
                    $type,
                    $name,
                    $namespace,
                    $this->getOptions($type)
                );

                $this->info("Generated test class at: {$testPath}");
            }

            return 0;
        } catch (\Exception $e) {
            $this->error($e->getMessage());
            return 1;
        }
    }

    protected function getNamespace(): string
    {
        $namespace = $this->option('namespace');
        
        if (empty($namespace)) {
            $type = $this->argument('type');
            $name = $this->argument('name');
            
            // Default namespace mapping
            $namespaces = [
                'command' => 'App\\Console\\Commands',
                'controller' => 'App\\Http\\Controllers',
                'model' => 'App\\Models',
                'service' => 'App\\Services',
                'event' => 'App\\Events',
                'listener' => 'App\\Listeners',
                'policy' => 'App\\Policies'
            ];

            $namespace = $namespaces[$type] ?? 'App';

            // Handle nested namespaces from the name
            if (str_contains($name, '/')) {
                $parts = explode('/', $name);
                $name = array_pop($parts);
                $namespace .= '\\' . implode('\\', array_map([Str::class, 'studly'], $parts));
            }
        }

        return $namespace;
    }

    protected function getOptions(string $type): array
    {
        $name = $this->argument('name');
        
        switch ($type) {
            case 'command':
                return [
                    'command' => Str::snake($name, ':'),
                    'description' => "The {$name} command"
                ];

            case 'controller':
                return [
                    'controller' => Str::snake($name, '.'),
                    'model' => Str::singular(class_basename($name))
                ];

            case 'model':
                return [
                    'table' => Str::snake(Str::plural(class_basename($name))),
                    'fillable' => '[]'
                ];

            case 'service':
                return [
                    'service' => Str::snake($name, '.'),
                    'dependencies' => ''
                ];

            case 'event':
                return [
                    'event' => Str::snake($name, '.'),
                    'properties' => ''
                ];

            case 'listener':
                return [
                    'listener' => Str::snake($name, '.'),
                    'event' => str_replace('Listener', '', class_basename($name))
                ];

            case 'policy':
                return [
                    'policy' => Str::snake($name, '.'),
                    'model' => str_replace('Policy', '', class_basename($name))
                ];

            default:
                return [];
        }
    }
} 