<?php

namespace LegalStudy\ModularInitialization\Initializers;

use LegalStudy\ModularInitialization\AbstractInitialization;

class FileSystemInitialization extends AbstractInitialization
{
    protected function doValidateConfiguration(): bool
    {
        if (!isset($this->config['base_path'])) {
            $this->status->addError('Base path not configured');
            return false;
        }

        if (!isset($this->config['permissions'])) {
            $this->status->addError('Permissions not configured');
            return false;
        }

        if (!isset($this->config['required_dirs']) || !is_array($this->config['required_dirs'])) {
            $this->status->addError('Required directories not configured');
            return false;
        }

        return true;
    }

    protected function doTestConnection(): bool
    {
        if (!is_dir($this->config['base_path'])) {
            if (!@mkdir($this->config['base_path'], $this->config['permissions'], true)) {
                $this->status->addError('Could not create base directory');
                return false;
            }
        }

        if (!is_writable($this->config['base_path'])) {
            $this->status->addError('Base directory is not writable');
            return false;
        }

        return true;
    }

    protected function doPerformInitialization(): void
    {
        foreach ($this->config['required_dirs'] as $dir) {
            $path = $this->config['base_path'] . DIRECTORY_SEPARATOR . $dir;
            
            if (!is_dir($path)) {
                if (!@mkdir($path, $this->config['permissions'], true)) {
                    throw new \RuntimeException("Could not create directory: {$path}");
                }
            }

            if (!is_writable($path)) {
                throw new \RuntimeException("Directory is not writable: {$path}");
            }
        }

        $this->status->setInitialized(true);
    }
} 