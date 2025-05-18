<?php

namespace Mcp\Core;

use Illuminate\Support\Facades\File;
use Illuminate\Support\Facades\Log;
use PHPUnit\TextUI\TestRunner;
use PHPUnit\Framework\TestSuite;
use PHPUnit\Framework\TestResult;
use PHPUnit\Framework\TestFailure;
use PHPUnit\Framework\TestError;

/**
 * TestAutomation handles automated test execution and reporting.
 * 
 * This class is responsible for:
 * - Automatically discovering and running tests
 * - Generating test reports
 * - Logging test results
 * - Managing test execution environment
 * 
 * @see Tests\Mcp\Core\TestAutomationTest
 */
class TestAutomation
{
    protected string $testDir;
    protected string $reportDir;
    protected string $errorDir;
    protected string $failureDir;
    protected TestRunner $runner;
    protected TestSuite $suite;

    public function __construct()
    {
        $this->testDir = base_path('tests');
        $this->reportDir = storage_path('test-reports');
        $this->errorDir = storage_path('.errors');
        $this->failureDir = storage_path('.failures');
        
        File::makeDirectory($this->reportDir, 0755, true, true);
        File::makeDirectory($this->errorDir, 0755, true, true);
        File::makeDirectory($this->failureDir, 0755, true, true);
        
        $this->runner = new TestRunner();
        $this->suite = new TestSuite('MCP Test Suite');
    }

    /**
     * Discovers and runs all tests.
     * 
     * @return array Test execution results
     */
    public function runAllTests(): array
    {
        $this->discoverTests();
        $result = $this->runner->run($this->suite);
        
        $this->logResults($result);
        return $this->formatResults($result);
    }

    /**
     * Discovers test files in the test directory.
     */
    protected function discoverTests(): void
    {
        $files = File::allFiles($this->testDir);
        
        foreach ($files as $file) {
            if ($file->getExtension() === 'php' && str_contains($file->getPathname(), 'Test.php')) {
                $this->suite->addTestFile($file->getPathname());
            }
        }
    }

    /**
     * Logs test execution results.
     * 
     * @param TestResult $result The test execution results
     */
    protected function logResults(TestResult $result): void
    {
        // Log failures
        foreach ($result->failures() as $failure) {
            $this->logFailure($failure);
        }
        
        // Log errors
        foreach ($result->errors() as $error) {
            $this->logError($error);
        }
        
        // Generate report
        $this->generateReport($result);
    }

    /**
     * Logs a test failure.
     * 
     * @param TestFailure $failure The test failure
     */
    protected function logFailure(TestFailure $failure): void
    {
        $timestamp = now()->format('Y-m-d_H-i-s');
        $filename = "failure_{$timestamp}.log";
        
        $content = sprintf(
            "[%s] Test Failure\nTest: %s\nMessage: %s\n",
            $timestamp,
            $failure->getTestName(),
            $failure->getExceptionMessage()
        );
        
        File::put($this->failureDir . '/' . $filename, $content);
        Log::error("Test Failure: {$failure->getTestName()}", ['failure' => $failure]);
    }

    /**
     * Logs a test error.
     * 
     * @param TestError $error The test error
     */
    protected function logError(TestError $error): void
    {
        $timestamp = now()->format('Y-m-d_H-i-s');
        $filename = "error_{$timestamp}.log";
        
        $content = sprintf(
            "[%s] Test Error\nTest: %s\nMessage: %s\n",
            $timestamp,
            $error->getTestName(),
            $error->getExceptionMessage()
        );
        
        File::put($this->errorDir . '/' . $filename, $content);
        Log::error("Test Error: {$error->getTestName()}", ['error' => $error]);
    }

    /**
     * Generates a test execution report.
     * 
     * @param TestResult $result The test execution results
     */
    protected function generateReport(TestResult $result): void
    {
        $report = [
            'timestamp' => now()->toIso8601String(),
            'total' => $result->count(),
            'passed' => $result->count() - $result->failureCount() - $result->errorCount(),
            'failed' => $result->failureCount(),
            'errors' => $result->errorCount(),
            'duration' => $result->time(),
            'memory' => memory_get_peak_usage(true)
        ];
        
        $filename = "report_{$report['timestamp']}.json";
        File::put($this->reportDir . '/' . $filename, json_encode($report, JSON_PRETTY_PRINT));
    }

    /**
     * Formats test results for return.
     * 
     * @param TestResult $result The test execution results
     * @return array Formatted results
     */
    protected function formatResults(TestResult $result): array
    {
        return [
            'total' => $result->count(),
            'passed' => $result->count() - $result->failureCount() - $result->errorCount(),
            'failed' => $result->failureCount(),
            'errors' => $result->errorCount(),
            'duration' => $result->time(),
            'memory' => memory_get_peak_usage(true)
        ];
    }
} 