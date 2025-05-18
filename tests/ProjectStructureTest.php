<?php

namespace Tests;

use PHPUnit\Framework\TestCase;
use RecursiveDirectoryIterator;
use RecursiveIteratorIterator;
use SplFileInfo;

/**
 * @coversNothing
 */
class ProjectStructureTest extends TestCase
{
    private const REQUIRED_DIRECTORIES = [
        'app',
        'bootstrap',
        'config',
        'database',
        'public',
        'resources',
        'routes',
        'storage',
        'tests',
        'vendor',
        '.checklist',
        '.completed',
        '.errors',
        '.failure',
        '.planning',
        '.research',
        '.test',
        '.unit',
        '.integration',
        '.refactoring',
        '.ux',
        '.ui',
        '.sniff',
        '.execution',
        '.initialization',
        '.tests',
        '.guide',
        '.qa',
        '.security',
        '.config',
        '.deployment',
        '.scripts',
        '.benchmarks',
        '.pytest_cache',
        '.phpunit.cache',
        '.api',
        '.checklists',
        '.controls',
        '.chaos',
        '.composer',
        '.notes',
        '.errors',
        '.prompts',
        '.testing',
        '.examples',
        '.experiments',
        '.logs',
        '.venv',
        'docs',
        'frontend',
        'migrations',
        'api',
        'templates',
        'var',
        'logs',
        'archive',
        'reports',
        'build',
        'scripts'
    ];

    private const REQUIRED_FILES = [
        'composer.json',
        'composer.lock',
        'phpunit.xml',
        '.phpunit.result.cache',
        '.coveragerc',
        'requirements-test.txt',
        'php.ini',
        'setup.ps1',
        'requirements-dev.txt',
        'requirements.test.txt',
        'app.db',
        'legal_study.db',
        'update_checklist.py',
        'run_verification.py',
        'verify_security.py',
        'verify_database.py',
        'verify_env.py',
        'alembic.ini',
        'monitor_resources.py',
        'run_tests.py',
        'pytest.ini',
        'run_monitored_tests.py',
        'monitor.py',
        'requirements.txt',
        'tsconfig.json',
        'package.json',
        'setup.py',
        '.gitignore',
        'phpcs.xml',
        'phpstan.neon',
        'LICENSE',
        'CHANGELOG.md',
        'CONTRIBUTING.md',
        'README.md',
        'console.php',
        'env.dev'
    ];

    public function setUp(): void
    {
        // Clear error and failure logs before each test
        $this->clearLogs();
    }

    private function clearLogs(): void
    {
        if (file_exists('.errors')) {
            array_map('unlink', glob('.errors/*'));
        }
        if (file_exists('.failure')) {
            array_map('unlink', glob('.failure/*'));
        }
    }

    private function logError(string $message): void
    {
        $timestamp = date('Y-m-d_H-i-s');
        file_put_contents(".errors/{$timestamp}.log", $message . PHP_EOL, FILE_APPEND);
    }

    private function logFailure(string $message): void
    {
        $timestamp = date('Y-m-d_H-i-s');
        file_put_contents(".failure/{$timestamp}.log", $message . PHP_EOL, FILE_APPEND);
    }

    public function testRequiredDirectoriesExist(): void
    {
        $missingDirs = [];
        foreach (self::REQUIRED_DIRECTORIES as $dir) {
            if (!is_dir($dir)) {
                $missingDirs[] = $dir;
                $this->logError("Missing required directory: {$dir}");
            }
        }

        if (!empty($missingDirs)) {
            $this->logFailure("Missing directories: " . implode(', ', $missingDirs));
            $this->fail("Missing required directories: " . implode(', ', $missingDirs));
        }
    }

    public function testRequiredFilesExist(): void
    {
        $missingFiles = [];
        foreach (self::REQUIRED_FILES as $file) {
            if (!file_exists($file)) {
                $missingFiles[] = $file;
                $this->logError("Missing required file: {$file}");
            }
        }

        if (!empty($missingFiles)) {
            $this->logFailure("Missing files: " . implode(', ', $missingFiles));
            $this->fail("Missing required files: " . implode(', ', $missingFiles));
        }
    }

    public function testVersionControlSetup(): void
    {
        if (!is_dir('.git')) {
            $this->logError("Git version control not initialized");
            $this->logFailure("Version control not set up");
            $this->fail("Git version control not initialized");
        }
    }

    public function testProjectDocumentation(): void
    {
        $requiredDocs = ['README.md', 'CONTRIBUTING.md', 'CHANGELOG.md', 'LICENSE'];
        $missingDocs = [];
        
        foreach ($requiredDocs as $doc) {
            if (!file_exists($doc)) {
                $missingDocs[] = $doc;
                $this->logError("Missing documentation file: {$doc}");
            }
        }

        if (!empty($missingDocs)) {
            $this->logFailure("Missing documentation files: " . implode(', ', $missingDocs));
            $this->fail("Missing required documentation files: " . implode(', ', $missingDocs));
        }
    }

    public function testDevelopmentEnvironment(): void
    {
        // Check for required development tools
        $requiredTools = [
            'composer' => 'Composer',
            'php' => 'PHP',
            'git' => 'Git'
        ];

        $missingTools = [];
        foreach ($requiredTools as $tool => $name) {
            $output = [];
            $returnVar = 0;
            exec("which {$tool}", $output, $returnVar);
            
            if ($returnVar !== 0) {
                $missingTools[] = $name;
                $this->logError("Missing development tool: {$name}");
            }
        }

        if (!empty($missingTools)) {
            $this->logFailure("Missing development tools: " . implode(', ', $missingTools));
            $this->fail("Missing required development tools: " . implode(', ', $missingTools));
        }
    }
} 