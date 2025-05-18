<?php

require_once __DIR__ . '/vendor/autoload.php';

use PHPUnit\Framework\TestSuite;
use PHPUnit\TextUI\TestRunner;
use PHPUnit\Framework\TestResult;
use PHPUnit\Framework\TestFailure;
use PHPUnit\Framework\Test;
use PHPUnit\Framework\AssertionFailedError;

// Ensure error and failure directories exist
if (!is_dir('.errors')) {
    mkdir('.errors', 0755, true);
}
if (!is_dir('.failure')) {
    mkdir('.failure', 0755, true);
}

// Clear existing logs
$clearLogs = function($dir) {
    if (is_dir($dir)) {
        $files = glob($dir . '/*');
        foreach ($files as $file) {
            if (is_file($file)) {
                unlink($file);
            }
        }
    }
};

$clearLogs('.errors');
$clearLogs('.failure');

// Create test suite
$suite = new TestSuite('Project Structure Tests');
$suite->addTestSuite('Tests\ProjectStructureTest');

// Run tests
$result = new TestResult();
$result->addListener(new class {
    public function addError(Test $test, Throwable $t, float $time): void
    {
        $timestamp = date('Y-m-d_H-i-s');
        $errorMessage = sprintf(
            "Error in %s: %s\n%s",
            $test->getName(),
            $t->getMessage(),
            $t->getTraceAsString()
        );
        file_put_contents(".errors/{$timestamp}.log", $errorMessage . PHP_EOL, FILE_APPEND);
    }

    public function addFailure(Test $test, AssertionFailedError $e, float $time): void
    {
        $timestamp = date('Y-m-d_H-i-s');
        $failureMessage = sprintf(
            "Failure in %s: %s\n%s",
            $test->getName(),
            $e->getMessage(),
            $e->getTraceAsString()
        );
        file_put_contents(".failure/{$timestamp}.log", $failureMessage . PHP_EOL, FILE_APPEND);
    }
});

$suite->run($result);

// Output results
echo "\nTest Results:\n";
echo "Tests run: " . $result->count() . "\n";
echo "Failures: " . count($result->failures()) . "\n";
echo "Errors: " . count($result->errors()) . "\n";
echo "Warnings: " . count($result->warnings()) . "\n";

if ($result->wasSuccessful()) {
    echo "\nAll tests passed!\n";
} else {
    echo "\nSome tests failed. Check .errors/ and .failure/ directories for details.\n";
    exit(1);
} 