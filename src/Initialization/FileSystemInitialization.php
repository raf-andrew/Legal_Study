<?php

namespace LegalStudy\Initialization;

use RuntimeException;

class FileSystemInitialization extends AbstractInitialization
{
    protected function doValidateConfiguration(array $config): bool
    {
        if (!isset($config['base_path']) || empty($config['base_path'])) {
            throw new \RuntimeException('Configuration validation failed: Base path is required');
        }

        if (!isset($config['permissions'])) {
            throw new \RuntimeException('Configuration validation failed: Permissions must be specified');
        }

        // Validate permissions (should be a valid octal number between 0000 and 0777)
        $permissions = octdec(sprintf('%04o', $config['permissions']));
        if ($permissions < 0 || $permissions > 0777) {
            throw new \RuntimeException('Configuration validation failed: Invalid permissions value');
        }

        if (!isset($config['required_dirs']) || !is_array($config['required_dirs']) || empty($config['required_dirs'])) {
            throw new \RuntimeException('Configuration validation failed: Required directories must be specified as a non-empty array');
        }

        // Validate that base_path exists or can be created
        if (!file_exists($config['base_path']) && !@mkdir($config['base_path'], $config['permissions'], true)) {
            throw new \RuntimeException('Configuration validation failed: Base path does not exist and cannot be created');
        }

        return true;
    }

    protected function doTestConnection(): bool
    {
        try {
            $testFile = $this->config['base_path'] . '/.test_' . uniqid();
            
            // Test write access
            if (file_put_contents($testFile, 'test') === false) {
                $this->addError('Failed to write test file');
                return false;
            }

            // Test read access
            if (file_get_contents($testFile) === false) {
                $this->addError('Failed to read test file');
                unlink($testFile);
                return false;
            }

            // Test delete access
            if (!unlink($testFile)) {
                $this->addError('Failed to delete test file');
                return false;
            }

            return true;
        } catch (\Exception $e) {
            $this->addError('File system connection test failed: ' . $e->getMessage());
            return false;
        }
    }

    protected function doPerformInitialization(): void
    {
        $basePath = $this->config['base_path'];
        $permissions = $this->config['permissions'];

        try {
            // Ensure base path exists
            if (!file_exists($basePath)) {
                if (!@mkdir($basePath, 0777, true)) {
                    throw new \RuntimeException("Failed to create base directory: {$basePath}");
                }
            } elseif (!is_dir($basePath)) {
                throw new \RuntimeException("Base path exists but is not a directory: {$basePath}");
            }

            // Set directory permissions explicitly
            if (!@chmod($basePath, $permissions)) {
                throw new \RuntimeException("Failed to set permissions on base directory: {$basePath}");
            }

            // Verify base directory permissions
            clearstatcache(true, $basePath);
            if (DIRECTORY_SEPARATOR === '\\') {
                if (!is_writable($basePath) || !is_readable($basePath)) {
                    throw new \RuntimeException("Base directory is not writable or readable: {$basePath}");
                }
            } else {
                $actualPerms = fileperms($basePath) & 0777;
                if ($actualPerms !== $permissions) {
                    throw new \RuntimeException(sprintf(
                        "Base directory has incorrect permissions. Expected: %o, Got: %o",
                        $permissions,
                        $actualPerms
                    ));
                }
            }

            // Create and set permissions for required directories
            foreach ($this->config['required_dirs'] as $dir) {
                $path = $basePath . DIRECTORY_SEPARATOR . $dir;
                
                if (!file_exists($path)) {
                    if (!@mkdir($path, 0777, true)) {
                        throw new \RuntimeException("Failed to create directory: {$path}");
                    }
                } elseif (!is_dir($path)) {
                    throw new \RuntimeException("Path exists but is not a directory: {$path}");
                }

                // Set directory permissions explicitly
                if (!@chmod($path, $permissions)) {
                    throw new \RuntimeException("Failed to set permissions on directory: {$path}");
                }

                // Verify directory permissions
                clearstatcache(true, $path);
                if (DIRECTORY_SEPARATOR === '\\') {
                    if (!is_writable($path) || !is_readable($path)) {
                        throw new \RuntimeException("Directory is not writable or readable: {$path}");
                    }
                } else {
                    $actualPerms = fileperms($path) & 0777;
                    if ($actualPerms !== $permissions) {
                        throw new \RuntimeException(sprintf(
                            "Directory %s has incorrect permissions. Expected: %o, Got: %o",
                            $dir,
                            $permissions,
                            $actualPerms
                        ));
                    }
                }

                // Add directory info to status
                $this->addData("dir_{$dir}", [
                    'path' => $path,
                    'permissions' => sprintf('%o', fileperms($path) & 0777),
                    'readable' => is_readable($path),
                    'writable' => is_writable($path)
                ]);
            }

            // Add base path info to status
            $this->addData('base_path', $basePath);
            $this->addData('permissions', sprintf('%o', $permissions));
        } catch (\Exception $e) {
            $this->addError($e->getMessage());
            throw $e;
        }
    }

    public function getBasePath(): string
    {
        return $this->config['base_path'] ?? '';
    }

    public function getRequiredDirs(): array
    {
        return $this->config['required_dirs'] ?? [];
    }
} 