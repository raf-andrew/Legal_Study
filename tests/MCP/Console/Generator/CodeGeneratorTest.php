<?php

namespace Tests\Mcp\Console\Generator;

use Mcp\Console\Generator\CodeGenerator;
use Tests\TestCase;
use Illuminate\Support\Facades\File;
use Illuminate\Support\Facades\Log;
use Mockery;

class CodeGeneratorTest extends TestCase
{
    private CodeGenerator $generator;
    private string $basePath;
    private string $tempDir;

    protected function setUp(): void
    {
        parent::setUp();
        
        $this->tempDir = sys_get_temp_dir() . '/mcp_generator_test_' . uniqid();
        mkdir($this->tempDir);
        
        $this->basePath = $this->tempDir;
        mkdir($this->tempDir . '/src');
        mkdir($this->tempDir . '/tests');
        
        $this->generator = new CodeGenerator($this->basePath);
        
        // Create template directory
        mkdir($this->tempDir . '/src/Mcp/Console/Generator/templates', 0777, true);
        
        // Create test templates
        $this->createTestTemplates();
    }

    protected function tearDown(): void
    {
        File::deleteDirectory($this->tempDir);
        parent::tearDown();
    }

    private function createTestTemplates(): void
    {
        $templates = [
            'command.stub' => "<?php\n\nnamespace {{namespace}};\n\nclass {{className}}\n{\n    // {{command}}\n}\n",
            'command_test.stub' => "<?php\n\nnamespace {{namespace}};\n\nclass {{className}}\n{\n    // Test for {{subjectClass}}\n}\n",
            'controller.stub' => "<?php\n\nnamespace {{namespace}};\n\nclass {{className}}\n{\n    // {{controller}}\n}\n",
            'controller_test.stub' => "<?php\n\nnamespace {{namespace}};\n\nclass {{className}}\n{\n    // Test for {{subjectClass}}\n}\n"
        ];

        foreach ($templates as $name => $content) {
            File::put($this->tempDir . '/src/Mcp/Console/Generator/templates/' . $name, $content);
        }
    }

    public function testGenerateClass(): void
    {
        Log::shouldReceive('info')
            ->once()
            ->with('Generated command class: App\\Commands\\TestCommand');

        $path = $this->generator->generateClass(
            'command',
            'TestCommand',
            'App\\Commands',
            ['command' => 'test:command']
        );

        $this->assertFileExists($path);
        $content = File::get($path);
        
        $this->assertStringContainsString('namespace App\\Commands;', $content);
        $this->assertStringContainsString('class TestCommand', $content);
        $this->assertStringContainsString('// test:command', $content);
    }

    public function testGenerateTest(): void
    {
        Log::shouldReceive('info')
            ->once()
            ->with('Generated test for command class: Tests\\App\\Commands\\TestCommandTest');

        $path = $this->generator->generateTest(
            'command',
            'TestCommand',
            'App\\Commands'
        );

        $this->assertFileExists($path);
        $content = File::get($path);
        
        $this->assertStringContainsString('namespace Tests\\App\\Commands;', $content);
        $this->assertStringContainsString('class TestCommandTest', $content);
        $this->assertStringContainsString('// Test for TestCommand', $content);
    }

    public function testGenerateClassWithExistingFile(): void
    {
        $path = $this->generator->generateClass(
            'command',
            'TestCommand',
            'App\\Commands'
        );

        $this->expectException(\RuntimeException::class);
        $this->expectExceptionMessage('File already exists: ' . $path);
        
        $this->generator->generateClass(
            'command',
            'TestCommand',
            'App\\Commands'
        );
    }

    public function testGenerateTestWithExistingFile(): void
    {
        $path = $this->generator->generateTest(
            'command',
            'TestCommand',
            'App\\Commands'
        );

        $this->expectException(\RuntimeException::class);
        $this->expectExceptionMessage('File already exists: ' . $path);
        
        $this->generator->generateTest(
            'command',
            'TestCommand',
            'App\\Commands'
        );
    }

    public function testGenerateClassWithUnknownTemplate(): void
    {
        $this->expectException(\InvalidArgumentException::class);
        $this->expectExceptionMessage('Unknown template type: unknown');
        
        $this->generator->generateClass(
            'unknown',
            'TestClass',
            'App'
        );
    }

    public function testGenerateTestWithUnknownTemplate(): void
    {
        $this->expectException(\InvalidArgumentException::class);
        $this->expectExceptionMessage('Unknown test template type: unknownTest');
        
        $this->generator->generateTest(
            'unknown',
            'TestClass',
            'App'
        );
    }

    public function testAddTemplate(): void
    {
        $template = "<?php\n\nnamespace {{namespace}};\n\nclass {{className}}\n{\n}\n";
        $this->generator->addTemplate('custom', $template);
        
        $this->assertEquals($template, $this->generator->getTemplate('custom'));
    }

    public function testGetNonexistentTemplate(): void
    {
        $this->assertNull($this->generator->getTemplate('nonexistent'));
    }

    public function testListTemplates(): void
    {
        $templates = $this->generator->listTemplates();
        
        $this->assertContains('command', $templates);
        $this->assertContains('commandTest', $templates);
        $this->assertContains('controller', $templates);
        $this->assertContains('controllerTest', $templates);
    }

    public function testGenerateClassInNestedNamespace(): void
    {
        Log::shouldReceive('info')
            ->once()
            ->with('Generated controller class: App\\Http\\Controllers\\Admin\\TestController');

        $path = $this->generator->generateClass(
            'controller',
            'TestController',
            'App\\Http\\Controllers\\Admin',
            ['controller' => 'admin.test']
        );

        $this->assertFileExists($path);
        $content = File::get($path);
        
        $this->assertStringContainsString('namespace App\\Http\\Controllers\\Admin;', $content);
        $this->assertStringContainsString('class TestController', $content);
        $this->assertStringContainsString('// admin.test', $content);
    }

    public function testGenerateTestInNestedNamespace(): void
    {
        Log::shouldReceive('info')
            ->once()
            ->with('Generated test for controller class: Tests\\App\\Http\\Controllers\\Admin\\TestControllerTest');

        $path = $this->generator->generateTest(
            'controller',
            'TestController',
            'App\\Http\\Controllers\\Admin'
        );

        $this->assertFileExists($path);
        $content = File::get($path);
        
        $this->assertStringContainsString('namespace Tests\\App\\Http\\Controllers\\Admin;', $content);
        $this->assertStringContainsString('class TestControllerTest', $content);
        $this->assertStringContainsString('// Test for TestController', $content);
    }
} 