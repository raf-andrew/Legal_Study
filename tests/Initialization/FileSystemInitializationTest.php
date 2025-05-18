<?php

namespace LegalStudy\ModularInitialization\Tests\Initialization;

use LegalStudy\ModularInitialization\Initializers\FileSystemInitialization;
use LegalStudy\ModularInitialization\Services\InitializationStatus;
use PHPUnit\Framework\TestCase;

/**
 * @covers \LegalStudy\ModularInitialization\Initializers\FileSystemInitialization
 * @covers \LegalStudy\ModularInitialization\AbstractInitialization
 * @covers \LegalStudy\ModularInitialization\Services\InitializationStatus
 */
class FileSystemInitializationTest extends TestCase
{
    protected FileSystemInitialization $filesystem;
    protected InitializationStatus $status;
    protected string $testBasePath;
    protected array $config;

    protected function setUp(): void
    {
        $this->testBasePath = sys_get_temp_dir() . '/legal_study_test_' . uniqid();
        $this->status = new InitializationStatus();
        $this->config = [
            'base_path' => $this->testBasePath,
            'permissions' => 0755,
            'required_dirs' => ['cache', 'logs', 'uploads']
        ];
        $this->filesystem = new FileSystemInitialization($this->status);
        $this->filesystem->setConfig($this->config);
    }

    protected function tearDown(): void
    {
        if (file_exists($this->testBasePath)) {
            $this->removeDirectory($this->testBasePath);
        }
    }

    private function removeDirectory(string $path): void
    {
        if (!file_exists($path)) {
            return;
        }

        $files = array_diff(scandir($path), ['.', '..']);
        foreach ($files as $file) {
            $filePath = $path . '/' . $file;
            if (is_dir($filePath)) {
                $this->removeDirectory($filePath);
            } else {
                unlink($filePath);
            }
        }
        rmdir($path);
    }

    public function test_validate_configuration_with_valid_config(): void
    {
        $this->assertTrue($this->filesystem->validateConfiguration($this->config));
    }

    public function test_validate_configuration_with_missing_base_path(): void
    {
        $this->expectException(\InvalidArgumentException::class);
        $config = $this->config;
        unset($config['base_path']);
        $this->filesystem->validateConfiguration($config);
    }

    public function test_validate_configuration_with_missing_permissions(): void
    {
        $this->expectException(\InvalidArgumentException::class);
        $config = $this->config;
        unset($config['permissions']);
        $this->filesystem->validateConfiguration($config);
    }

    public function test_validate_configuration_with_missing_required_dirs(): void
    {
        $this->expectException(\InvalidArgumentException::class);
        $config = $this->config;
        unset($config['required_dirs']);
        $this->filesystem->validateConfiguration($config);
    }

    public function test_validate_configuration_with_empty_required_dirs(): void
    {
        $this->expectException(\InvalidArgumentException::class);
        $config = $this->config;
        $config['required_dirs'] = [];
        $this->filesystem->validateConfiguration($config);
    }

    public function test_validate_configuration_with_invalid_permissions(): void
    {
        $this->expectException(\InvalidArgumentException::class);
        $config = $this->config;
        $config['permissions'] = -1;
        $this->filesystem->validateConfiguration($config);
    }

    public function test_test_connection_with_valid_config(): void
    {
        // Create base directory first
        if (!file_exists($this->testBasePath)) {
            mkdir($this->testBasePath, 0755, true);
        }

        $this->assertTrue($this->filesystem->testConnection());
        $this->assertFalse($this->status->isFailed());
    }

    public function test_perform_initialization_creates_directories(): void
    {
        $this->filesystem->performInitialization();

        $this->assertTrue(file_exists($this->testBasePath));
        $this->assertTrue(file_exists($this->testBasePath . '/cache'));
        $this->assertTrue(file_exists($this->testBasePath . '/logs'));
        $this->assertTrue(file_exists($this->testBasePath . '/uploads'));

        $this->assertTrue($this->status->isInitialized());
        $this->assertEquals($this->testBasePath, $this->status->getData('base_path'));
        $this->assertEquals(['cache', 'logs', 'uploads'], $this->status->getData('created_dirs'));
    }

    public function test_perform_initialization_sets_permissions(): void
    {
        $this->filesystem->performInitialization();

        // On Windows, the permissions are always 0777
        $expectedPermissions = PHP_OS_FAMILY === 'Windows' ? '0777' : '0755';
        
        $this->assertEquals($expectedPermissions, substr(sprintf('%o', fileperms($this->testBasePath)), -4));
        $this->assertEquals($expectedPermissions, substr(sprintf('%o', fileperms($this->testBasePath . '/cache')), -4));
        $this->assertEquals($expectedPermissions, substr(sprintf('%o', fileperms($this->testBasePath . '/logs')), -4));
        $this->assertEquals($expectedPermissions, substr(sprintf('%o', fileperms($this->testBasePath . '/uploads')), -4));
    }
} 