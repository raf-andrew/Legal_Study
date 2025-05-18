<?php

namespace Mcp\Core;

use Illuminate\Support\Facades\File;
use Illuminate\Support\Facades\Log;
use Illuminate\Support\Collection;
use Carbon\Carbon;

/**
 * FailureTracker handles tracking and analysis of test failures and errors.
 * 
 * This class is responsible for:
 * - Tracking test failures and errors
 * - Analyzing failure patterns
 * - Generating failure reports
 * - Managing failure history
 * 
 * @see Tests\Mcp\Core\FailureTrackerTest
 */
class FailureTracker
{
    protected string $failureDir;
    protected string $errorDir;
    protected string $reportDir;
    protected Collection $failures;
    protected Collection $errors;

    public function __construct()
    {
        $this->failureDir = storage_path('.failures');
        $this->errorDir = storage_path('.errors');
        $this->reportDir = storage_path('failure-reports');
        
        File::makeDirectory($this->failureDir, 0755, true, true);
        File::makeDirectory($this->errorDir, 0755, true, true);
        File::makeDirectory($this->reportDir, 0755, true, true);
        
        $this->failures = collect();
        $this->errors = collect();
    }

    /**
     * Tracks a test failure.
     * 
     * @param string $testName The name of the failing test
     * @param string $message The failure message
     * @param array $context Additional failure context
     */
    public function trackFailure(string $testName, string $message, array $context = []): void
    {
        $failure = [
            'test_name' => $testName,
            'message' => $message,
            'context' => $context,
            'timestamp' => now()->toIso8601String()
        ];
        
        $this->failures->push($failure);
        $this->logFailure($failure);
    }

    /**
     * Tracks a test error.
     * 
     * @param string $testName The name of the test with error
     * @param string $message The error message
     * @param array $context Additional error context
     */
    public function trackError(string $testName, string $message, array $context = []): void
    {
        $error = [
            'test_name' => $testName,
            'message' => $message,
            'context' => $context,
            'timestamp' => now()->toIso8601String()
        ];
        
        $this->errors->push($error);
        $this->logError($error);
    }

    /**
     * Logs a failure to the filesystem.
     * 
     * @param array $failure The failure data
     */
    protected function logFailure(array $failure): void
    {
        $timestamp = now()->format('Y-m-d_H-i-s');
        $filename = "failure_{$timestamp}.log";
        
        $content = sprintf(
            "[%s] Test Failure\nTest: %s\nMessage: %s\nContext: %s\n",
            $failure['timestamp'],
            $failure['test_name'],
            $failure['message'],
            json_encode($failure['context'], JSON_PRETTY_PRINT)
        );
        
        File::put($this->failureDir . '/' . $filename, $content);
        Log::error("Test Failure: {$failure['test_name']}", $failure);
    }

    /**
     * Logs an error to the filesystem.
     * 
     * @param array $error The error data
     */
    protected function logError(array $error): void
    {
        $timestamp = now()->format('Y-m-d_H-i-s');
        $filename = "error_{$timestamp}.log";
        
        $content = sprintf(
            "[%s] Test Error\nTest: %s\nMessage: %s\nContext: %s\n",
            $error['timestamp'],
            $error['test_name'],
            $error['message'],
            json_encode($error['context'], JSON_PRETTY_PRINT)
        );
        
        File::put($this->errorDir . '/' . $filename, $content);
        Log::error("Test Error: {$error['test_name']}", $error);
    }

    /**
     * Analyzes failure patterns.
     * 
     * @return array Analysis results
     */
    public function analyzeFailures(): array
    {
        $analysis = [
            'total_failures' => $this->failures->count(),
            'total_errors' => $this->errors->count(),
            'failure_patterns' => [],
            'error_patterns' => [],
            'recent_failures' => [],
            'recent_errors' => []
        ];
        
        // Analyze failure patterns
        $this->failures->groupBy('test_name')->each(function ($failures, $testName) use (&$analysis) {
            $analysis['failure_patterns'][$testName] = [
                'count' => $failures->count(),
                'last_occurrence' => $failures->last()['timestamp'],
                'messages' => $failures->pluck('message')->unique()->values()
            ];
        });
        
        // Analyze error patterns
        $this->errors->groupBy('test_name')->each(function ($errors, $testName) use (&$analysis) {
            $analysis['error_patterns'][$testName] = [
                'count' => $errors->count(),
                'last_occurrence' => $errors->last()['timestamp'],
                'messages' => $errors->pluck('message')->unique()->values()
            ];
        });
        
        // Get recent failures and errors
        $analysis['recent_failures'] = $this->failures->sortByDesc('timestamp')->take(10)->values();
        $analysis['recent_errors'] = $this->errors->sortByDesc('timestamp')->take(10)->values();
        
        return $analysis;
    }

    /**
     * Generates a failure report.
     * 
     * @return string Path to the generated report
     */
    public function generateReport(): string
    {
        $analysis = $this->analyzeFailures();
        $timestamp = now()->format('Y-m-d_H-i-s');
        $filename = "failure_report_{$timestamp}.json";
        $path = $this->reportDir . '/' . $filename;
        
        File::put($path, json_encode($analysis, JSON_PRETTY_PRINT));
        
        return $path;
    }

    /**
     * Gets failure history for a specific test.
     * 
     * @param string $testName The test name
     * @return array Failure history
     */
    public function getTestHistory(string $testName): array
    {
        return [
            'failures' => $this->failures->where('test_name', $testName)->values(),
            'errors' => $this->errors->where('test_name', $testName)->values()
        ];
    }

    /**
     * Cleans up old failure and error logs.
     * 
     * @param int $days Number of days to keep logs
     */
    public function cleanupOldLogs(int $days = 30): void
    {
        $cutoff = now()->subDays($days);
        
        // Cleanup failure logs
        foreach (File::files($this->failureDir) as $file) {
            if (Carbon::createFromTimestamp($file->getMTime())->lt($cutoff)) {
                File::delete($file->getPathname());
            }
        }
        
        // Cleanup error logs
        foreach (File::files($this->errorDir) as $file) {
            if (Carbon::createFromTimestamp($file->getMTime())->lt($cutoff)) {
                File::delete($file->getPathname());
            }
        }
    }
} 