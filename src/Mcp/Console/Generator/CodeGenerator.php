<?php

namespace Mcp\Console\Generator;

use Illuminate\Support\Str;
use Illuminate\Support\Facades\File;
use Illuminate\Support\Facades\Log;

class CodeGenerator
{
    protected string $basePath;
    protected array $templates = [];
    protected array $replacements = [];

    public function __construct(string $basePath)
    {
        $this->basePath = $basePath;
        $this->loadTemplates();
    }

    public function generateClass(
        string $type,
        string $name,
        string $namespace,
        array $options = []
    ): string {
        if (!isset($this->templates[$type])) {
            throw new \InvalidArgumentException("Unknown template type: $type");
        }

        $template = $this->templates[$type];
        $className = $this->getClassName($name);
        $path = $this->getClassPath($namespace, $className);

        if (File::exists($path)) {
            throw new \RuntimeException("File already exists: $path");
        }

        $content = $this->processTemplate($template, [
            'namespace' => $namespace,
            'className' => $className,
            'options' => $options
        ]);

        File::put($path, $content);
        Log::info("Generated $type class: $namespace\\$className");

        return $path;
    }

    public function generateTest(
        string $type,
        string $name,
        string $namespace,
        array $options = []
    ): string {
        $testType = $type . 'Test';
        if (!isset($this->templates[$testType])) {
            throw new \InvalidArgumentException("Unknown test template type: $testType");
        }

        $template = $this->templates[$testType];
        $className = $this->getClassName($name) . 'Test';
        $path = $this->getTestPath($namespace, $className);

        if (File::exists($path)) {
            throw new \RuntimeException("File already exists: $path");
        }

        $content = $this->processTemplate($template, [
            'namespace' => "Tests\\$namespace",
            'className' => $className,
            'subjectClass' => $this->getClassName($name),
            'subjectNamespace' => $namespace,
            'options' => $options
        ]);

        File::put($path, $content);
        Log::info("Generated test for $type class: Tests\\$namespace\\$className");

        return $path;
    }

    protected function loadTemplates(): void
    {
        $this->templates = [
            'command' => File::get(__DIR__ . '/templates/command.stub'),
            'commandTest' => File::get(__DIR__ . '/templates/command_test.stub'),
            'controller' => File::get(__DIR__ . '/templates/controller.stub'),
            'controllerTest' => File::get(__DIR__ . '/templates/controller_test.stub'),
            'model' => File::get(__DIR__ . '/templates/model.stub'),
            'modelTest' => File::get(__DIR__ . '/templates/model_test.stub'),
            'service' => File::get(__DIR__ . '/templates/service.stub'),
            'serviceTest' => File::get(__DIR__ . '/templates/service_test.stub'),
            'event' => File::get(__DIR__ . '/templates/event.stub'),
            'eventTest' => File::get(__DIR__ . '/templates/event_test.stub'),
            'listener' => File::get(__DIR__ . '/templates/listener.stub'),
            'listenerTest' => File::get(__DIR__ . '/templates/listener_test.stub'),
            'policy' => File::get(__DIR__ . '/templates/policy.stub'),
            'policyTest' => File::get(__DIR__ . '/templates/policy_test.stub')
        ];
    }

    protected function getClassName(string $name): string
    {
        return Str::studly($name);
    }

    protected function getClassPath(string $namespace, string $className): string
    {
        $path = str_replace('\\', '/', $namespace);
        return $this->basePath . '/src/' . $path . '/' . $className . '.php';
    }

    protected function getTestPath(string $namespace, string $className): string
    {
        $path = str_replace('\\', '/', $namespace);
        return $this->basePath . '/tests/' . $path . '/' . $className . '.php';
    }

    protected function processTemplate(string $template, array $data): string
    {
        $replacements = [
            '{{namespace}}' => $data['namespace'],
            '{{className}}' => $data['className']
        ];

        if (isset($data['subjectNamespace'])) {
            $replacements['{{subjectNamespace}}'] = $data['subjectNamespace'];
            $replacements['{{subjectClass}}'] = $data['subjectClass'];
        }

        foreach ($data['options'] as $key => $value) {
            $replacements["{{$key}}"] = $value;
        }

        return str_replace(
            array_keys($replacements),
            array_values($replacements),
            $template
        );
    }

    public function addTemplate(string $type, string $template): void
    {
        $this->templates[$type] = $template;
    }

    public function getTemplate(string $type): ?string
    {
        return $this->templates[$type] ?? null;
    }

    public function listTemplates(): array
    {
        return array_keys($this->templates);
    }
} 