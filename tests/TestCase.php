<?php

namespace Tests;

use Illuminate\Foundation\Testing\TestCase as BaseTestCase;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Illuminate\Support\Facades\File;

abstract class TestCase extends BaseTestCase
{
    use CreatesApplication, RefreshDatabase;

    /**
     * Setup the test environment.
     */
    protected function setUp(): void
    {
        parent::setUp();

        // Ensure test directories exist
        $directories = [
            '.codespaces/services',
            '.codespaces/state',
            '.codespaces/logs',
            '.codespaces/verification',
            '.codespaces/complete'
        ];

        foreach ($directories as $directory) {
            if (!File::exists($directory)) {
                File::makeDirectory($directory, 0755, true);
            }
        }
    }

    /**
     * Clean up the test environment.
     */
    protected function tearDown(): void
    {
        // Clean up test directories
        $directories = [
            '.codespaces/state',
            '.codespaces/logs',
            '.codespaces/verification',
            '.codespaces/complete'
        ];

        foreach ($directories as $directory) {
            if (File::exists($directory)) {
                File::deleteDirectory($directory);
            }
        }

        parent::tearDown();
    }

    /**
     * Handle test failures and errors.
     */
    protected function onNotSuccessfulTest(\Throwable $t): never
    {
        // Log errors
        $timestamp = date('Y-m-d_H-i-s');
        $errorMessage = sprintf(
            "Error in %s::%s: %s\n%s",
            static::class,
            $this->getName(),
            $t->getMessage(),
            $t->getTraceAsString()
        );
        file_put_contents(".errors/{$timestamp}.log", $errorMessage . PHP_EOL, FILE_APPEND);

        // Log failures
        if ($t instanceof \PHPUnit\Framework\AssertionFailedError) {
            $failureMessage = sprintf(
                "Failure in %s::%s: %s\n%s",
                static::class,
                $this->getName(),
                $t->getMessage(),
                $t->getTraceAsString()
            );
            file_put_contents(".failure/{$timestamp}.log", $failureMessage . PHP_EOL, FILE_APPEND);
        }

        parent::onNotSuccessfulTest($t);
    }
}
