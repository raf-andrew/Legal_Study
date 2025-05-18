<?php

namespace LegalStudy\ModularInitialization\Tests\Unit\Initializers;

use LegalStudy\ModularInitialization\Initializers\FileSystemInitialization;
use Orchestra\Testbench\TestCase;
use RuntimeException;

class FileSystemInitializationTest extends TestCase
{
    private FileSystemInitialization $initialization;
    private string $testDir;

    protected function setUp(): void
    {
        parent::setUp();
        
        $this->initialization = new FileSystemInitialization();
        $this->testDir = sys_get_temp_dir() . '/test_fs_init_' . uniqid();
        
        // Create test directory with explicit permissions
        if (!file_exists($this->testDir)) {
            if (!mkdir($this->testDir, 0755, true)) {
                throw new RuntimeException('Failed to create test directory');
            }
        }
        
        // On Windows, we need to use icacls to set permissions
        if (DIRECTORY_SEPARATOR === '\\') {
            // Get current user
            $user = get_current_user();
            
            // Set permissions using icacls
            $command = sprintf('icacls "%s" /grant "%s":(OI)(CI)F /T', $this->testDir, $user);
            exec($command, $output, $returnVar);
            
            if ($returnVar !== 0) {
                throw new RuntimeException('Failed to set directory permissions using icacls');
            }
        } else {
            // Set directory permissions explicitly
            if (!chmod($this->testDir, 0755)) {
                throw new RuntimeException('Failed to set test directory permissions');
            }
            
            // Double check the permissions
            clearstatcache(true, $this->testDir);
            $actualPerms = fileperms($this->testDir) & 0777;
            if ($actualPerms !== 0755) {
                throw new RuntimeException(sprintf(
                    'Directory permissions mismatch. Expected: %o, Got: %o',
                    0755,
                    $actualPerms
                ));
            }
        }
    }

    protected function tearDown(): void
    {
        parent::tearDown();
        
        if (file_exists($this->testDir)) {
            // On Windows, we need to take ownership and grant full permissions before deleting
            if (DIRECTORY_SEPARATOR === '\\') {
                $user = get_current_user();
                exec(sprintf('takeown /F "%s" /R /D Y', $this->testDir));
                exec(sprintf('icacls "%s" /grant "%s":(OI)(CI)F /T', $this->testDir, $user));
            }
            
            $this->removeDirectory($this->testDir);
        }
    }

    private function removeDirectory(string $dir): void
    {
        if (!file_exists($dir)) {
            return;
        }

        $files = array_diff(scandir($dir), ['.', '..']);
        foreach ($files as $file) {
            $path = $dir . '/' . $file;
            if (is_dir($path)) {
                $this->removeDirectory($path);
            } else {
                unlink($path);
            }
        }
        rmdir($dir);
    }

    public function testValidateConfiguration(): void
    {
        // Test valid configuration
        $validConfig = [
            'base_path' => $this->testDir,
            'permissions' => 0755,
            'required_dirs' => ['cache', 'logs', 'uploads']
        ];

        $this->assertTrue($this->initialization->validateConfiguration($validConfig));

        // Test missing required_dirs
        $invalidConfig = [
            'base_path' => $this->testDir,
            'permissions' => 0755
            // Missing required_dirs
        ];

        $this->expectException(RuntimeException::class);
        $this->expectExceptionMessage('Required directories must be specified as a non-empty array');
        $this->initialization->validateConfiguration($invalidConfig);
    }

    public function testTestConnection(): void
    {
        $config = [
            'base_path' => $this->testDir,
            'permissions' => 0755,
            'required_dirs' => ['test']
        ];

        $this->initialization->validateConfiguration($config);
        $this->assertTrue($this->initialization->testConnection());
    }

    public function testPerformInitialization(): void
    {
        $config = [
            'base_path' => $this->testDir,
            'permissions' => 0755,
            'required_dirs' => ['cache', 'logs', 'uploads']
        ];

        $this->initialization->validateConfiguration($config);
        $this->initialization->performInitialization();

        // Verify directories were created with correct permissions
        foreach ($config['required_dirs'] as $dir) {
            $path = $this->testDir . '/' . $dir;
            $this->assertTrue(is_dir($path), "Directory $dir was not created");
            
            // On Windows, we verify using is_writable and is_readable
            if (DIRECTORY_SEPARATOR === '\\') {
                $this->assertTrue(is_writable($path), "Directory $dir is not writable");
                $this->assertTrue(is_readable($path), "Directory $dir is not readable");
            } else {
                $this->assertEquals(
                    0755,
                    fileperms($path) & 0777,
                    sprintf(
                        "Directory %s has incorrect permissions. Expected: %o, Got: %o",
                        $dir,
                        0755,
                        fileperms($path) & 0777
                    )
                );
            }
        }
    }

    public function testErrorHandling(): void
    {
        $config = [
            'base_path' => $this->testDir,
            'permissions' => 0755,
            'required_dirs' => [
                'cache',
                'logs',
                'uploads'
            ]
        ];

        // Create a file where a directory should be
        $cachePath = $this->testDir . '/cache';
        file_put_contents($cachePath, 'test');

        try {
            $this->initialization->validateConfiguration($config);
            $this->initialization->performInitialization();
            $this->fail('Expected RuntimeException was not thrown');
        } catch (RuntimeException $e) {
            $this->assertStringContainsString('exists but is not a directory', $e->getMessage());
            $this->assertTrue($this->initialization->getStatus()->isFailed());
            $this->assertNotEmpty($this->initialization->getStatus()->getErrors());
        } finally {
            // Clean up
            if (file_exists($cachePath)) {
                unlink($cachePath);
            }
        }
    }

    public function testDirectoryPermissions(): void
    {
        $config = [
            'base_path' => $this->testDir,
            'permissions' => 0755,
            'required_dirs' => ['test_dir']
        ];

        $this->initialization->validateConfiguration($config);
        $this->initialization->performInitialization();

        $testDirPath = $this->testDir . '/test_dir';
        $this->assertTrue(is_dir($testDirPath));
        
        // On Windows, we verify using is_writable and is_readable
        if (DIRECTORY_SEPARATOR === '\\') {
            $this->assertTrue(is_writable($testDirPath), "Directory is not writable");
            $this->assertTrue(is_readable($testDirPath), "Directory is not readable");
        } else {
            $actualPermissions = fileperms($testDirPath) & 0777;
            $expectedPermissions = 0755;
            
            $this->assertEquals(
                $expectedPermissions,
                $actualPermissions,
                sprintf(
                    'Directory permissions mismatch. Expected: %o, Got: %o',
                    $expectedPermissions,
                    $actualPermissions
                )
            );
        }
    }
} 