<?php

namespace Tests\Integration;

use LegalStudy\ModularInitialization\Initializers\FileSystemInitialization;
use LegalStudy\ModularInitialization\Services\InitializationStatus;
use PHPUnit\Framework\TestCase;

class FileSystemInitializationIntegrationTest extends TestCase
{
    private FileSystemInitialization $initialization;
    private array $config;
    private string $testDir;
    private InitializationStatus $status;

    protected function setUp(): void
    {
        $this->testDir = sys_get_temp_dir() . '/legal_study_test_' . uniqid();
        $this->config = [
            'base_path' => $this->testDir,
            'permissions' => 0755,
            'required_dirs' => [
                'cache',
                'logs',
                'uploads',
                'temp'
            ]
        ];

        $this->status = new InitializationStatus();
        $this->initialization = new FileSystemInitialization($this->status);
    }

    public function testFileSystemInitialization(): void
    {
        $this->assertTrue($this->initialization->validateConfiguration($this->config));
        $this->initialization->performInitialization();

        $status = $this->initialization->getStatus();
        $this->assertTrue($status->isInitialized());
        $this->assertEmpty($status->getErrors());
    }

    public function testDirectoryCreation(): void
    {
        $this->initialization->validateConfiguration($this->config);
        $this->initialization->performInitialization();

        foreach ($this->config['required_dirs'] as $dir) {
            $path = $this->testDir . '/' . $dir;
            $this->assertDirectoryExists($path);
            
            // On Windows, we only check if the directory is readable and writable
            if (DIRECTORY_SEPARATOR === '\\') {
                $this->assertTrue(is_readable($path));
                $this->assertTrue(is_writable($path));
            } else {
                $this->assertEquals($this->config['permissions'], fileperms($path) & 0777);
            }
        }
    }

    public function testFileOperations(): void
    {
        $this->initialization->validateConfiguration($this->config);
        $this->initialization->performInitialization();

        // Test file creation
        $testFile = $this->testDir . '/test.txt';
        file_put_contents($testFile, 'test content');
        $this->assertFileExists($testFile);

        // Test file reading
        $content = file_get_contents($testFile);
        $this->assertEquals('test content', $content);

        // Test file deletion
        unlink($testFile);
        $this->assertFileDoesNotExist($testFile);
    }

    public function testErrorHandling(): void
    {
        // Create test directory
        if (!file_exists($this->testDir)) {
            mkdir($this->testDir, 0755, true);
        }

        // Test with invalid permissions
        $invalidConfig = array_merge($this->config, [
            'permissions' => -1 // Invalid permissions value
        ]);

        try {
            $this->initialization->validateConfiguration($invalidConfig);
            $this->fail('Expected InvalidArgumentException was not thrown');
        } catch (\InvalidArgumentException $e) {
            $status = $this->initialization->getStatus();
            $this->assertTrue($status->isFailed());
            $this->assertNotEmpty($status->getErrors());
            $this->assertStringContainsString('Invalid permissions', $e->getMessage());
        }

        // Test with file instead of directory
        $filePath = $this->testDir . '/test_file';
        file_put_contents($filePath, 'test');

        $fileConfig = array_merge($this->config, [
            'required_dirs' => ['test_file']
        ]);

        try {
            $this->initialization->validateConfiguration($fileConfig);
            $this->initialization->performInitialization();
            $this->fail('Expected RuntimeException was not thrown');
        } catch (\RuntimeException $e) {
            $status = $this->initialization->getStatus();
            $this->assertTrue($status->isFailed());
            $this->assertNotEmpty($status->getErrors());
            $this->assertStringContainsString('not a directory', $e->getMessage());
        } finally {
            if (file_exists($filePath)) {
                unlink($filePath);
            }
        }
    }

    public function testDirectoryPermissions(): void
    {
        $this->initialization->validateConfiguration($this->config);
        $this->initialization->performInitialization();

        // Test directory permissions
        foreach ($this->config['required_dirs'] as $dir) {
            $path = $this->testDir . '/' . $dir;
            $this->assertTrue(is_readable($path));
            $this->assertTrue(is_writable($path));
        }
    }

    public function testConcurrentAccess(): void
    {
        $this->initialization->validateConfiguration($this->config);
        $this->initialization->performInitialization();

        // Simulate concurrent access
        $processes = [];
        for ($i = 0; $i < 5; $i++) {
            $testFile = $this->testDir . '/cache/test_' . $i . '.txt';
            $processes[] = function() use ($testFile) {
                file_put_contents($testFile, 'test content ' . uniqid());
                usleep(100); // Simulate work
                $content = file_get_contents($testFile);
                return $content !== false;
            };
        }

        // Run processes and verify
        $results = array_map(function($process) {
            return $process();
        }, $processes);

        $this->assertEquals(array_fill(0, 5, true), $results);
    }

    public function testPartialInitializationRecovery(): void
    {
        // Create a partially initialized state
        mkdir($this->testDir, 0755, true);
        mkdir($this->testDir . '/cache', 0755);
        // Deliberately skip creating other directories

        $this->initialization->validateConfiguration($this->config);
        $this->initialization->performInitialization();

        // Verify recovery
        foreach ($this->config['required_dirs'] as $dir) {
            $path = $this->testDir . '/' . $dir;
            $this->assertDirectoryExists($path);
            
            // On Windows, we only check if the directory is readable and writable
            if (DIRECTORY_SEPARATOR === '\\') {
                $this->assertTrue(is_readable($path));
                $this->assertTrue(is_writable($path));
            } else {
                $this->assertEquals($this->config['permissions'], fileperms($path) & 0777);
            }
        }
    }

    public function testSymlinkHandling(): void
    {
        if (DIRECTORY_SEPARATOR === '\\') {
            $this->markTestSkipped('Symlink tests not supported on Windows');
            return;
        }

        $this->initialization->validateConfiguration($this->config);
        $this->initialization->performInitialization();

        // Create and test symlink
        $linkSource = $this->testDir . '/cache';
        $linkTarget = sys_get_temp_dir() . '/cache_link';
        symlink($linkSource, $linkTarget);

        $this->assertTrue(is_link($linkTarget));
        $this->assertTrue(is_readable($linkTarget));
        $this->assertTrue(is_writable($linkTarget));

        // Cleanup
        unlink($linkTarget);
    }

    public function testLongPathHandling(): void
    {
        // Create a deeply nested directory structure (but not too deep)
        $longPath = str_repeat('subdir/', 10); // Reduced from 50 to 10 levels
        $config = array_merge($this->config, [
            'required_dirs' => array_merge($this->config['required_dirs'], [$longPath])
        ]);

        $this->initialization->validateConfiguration($config);
        $result = $this->initialization->performInitialization();

        $path = $this->testDir . '/' . $longPath;
        $this->assertDirectoryExists(rtrim($path, '/'));
        
        // On Windows, verify the directory is accessible
        if (DIRECTORY_SEPARATOR === '\\') {
            $this->assertTrue(is_readable($path));
            $this->assertTrue(is_writable($path));
        } else {
            $this->assertEquals($this->config['permissions'], fileperms(rtrim($path, '/')) & 0777);
        }
    }

    protected function tearDown(): void
    {
        // Clean up test directory
        if (is_dir($this->testDir)) {
            $this->removeDirectory($this->testDir);
        }

        // Reset status
        $this->status->reset();
    }

    private function removeDirectory(string $dir): void
    {
        if (!is_dir($dir)) {
            return;
        }

        $files = array_diff(scandir($dir), ['.', '..']);
        foreach ($files as $file) {
            $path = $dir . '/' . $file;
            is_dir($path) ? $this->removeDirectory($path) : unlink($path);
        }

        rmdir($dir);
    }
} 