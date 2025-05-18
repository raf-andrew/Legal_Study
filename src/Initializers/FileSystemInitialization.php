<?php

namespace LegalStudy\ModularInitialization\Initializers;

use LegalStudy\ModularInitialization\AbstractInitialization;
use LegalStudy\ModularInitialization\Services\InitializationStatus;

class FileSystemInitialization extends AbstractInitialization
{
    protected function doValidateConfiguration(): void
    {
        $requiredKeys = ['base_path', 'permissions', 'required_dirs'];
        foreach ($requiredKeys as $key) {
            if (!isset($this->config[$key])) {
                $this->addError("Missing required configuration key: {$key}");
            }
        }

        if (isset($this->config['base_path']) && !is_string($this->config['base_path'])) {
            $this->addError("Base path must be a string");
        }

        if (isset($this->config['permissions']) && !is_array($this->config['permissions'])) {
            $this->addError("Permissions must be an array");
        }

        if (isset($this->config['required_dirs']) && !is_array($this->config['required_dirs'])) {
            $this->addError("Required directories must be an array");
        }
    }

    protected function doTestConnection(): bool
    {
        try {
            $basePath = $this->getBasePath();
            
            // Test write access
            $testFile = $basePath . '/test_' . uniqid() . '.tmp';
            if (file_put_contents($testFile, 'test') === false) {
                throw new \RuntimeException("Failed to write test file");
            }
            
            // Test read access
            if (file_get_contents($testFile) !== 'test') {
                throw new \RuntimeException("Failed to read test file");
            }
            
            // Test delete access
            if (!unlink($testFile)) {
                throw new \RuntimeException("Failed to delete test file");
            }
            
            return true;
        } catch (\Exception $e) {
            $this->addError("Connection test failed: " . $e->getMessage());
            return false;
        }
    }

    protected function doPerformInitialization(): void
    {
        try {
            $basePath = $this->getBasePath();
            $requiredDirs = $this->getRequiredDirectories();
            
            // Create required directories
            foreach ($requiredDirs as $dir) {
                $fullPath = $basePath . '/' . $dir;
                if (!file_exists($fullPath)) {
                    if (!mkdir($fullPath, 0755, true)) {
                        throw new \RuntimeException("Failed to create directory: {$dir}");
                    }
                }
            }
            
            // Set permissions
            $this->setDirectoryPermissions($basePath);
        } catch (\Exception $e) {
            $this->addError("Initialization failed: " . $e->getMessage());
            throw $e;
        }
    }

    private function setDirectoryPermissions(string $path): void
    {
        $permissions = $this->config['permissions'];
        
        if (isset($permissions['dir'])) {
            if (!chmod($path, $permissions['dir'])) {
                throw new \RuntimeException("Failed to set directory permissions for: {$path}");
            }
        }
        
        if (isset($permissions['file'])) {
            $files = new \RecursiveIteratorIterator(
                new \RecursiveDirectoryIterator($path),
                \RecursiveIteratorIterator::SELF_FIRST
            );
            
            foreach ($files as $file) {
                if ($file->isFile()) {
                    if (!chmod($file->getPathname(), $permissions['file'])) {
                        throw new \RuntimeException("Failed to set file permissions for: {$file->getPathname()}");
                    }
                }
            }
        }
    }

    public function getBasePath(): string
    {
        return $this->config['base_path'];
    }

    public function getRequiredDirectories(): array
    {
        return $this->config['required_dirs'];
    }
} 