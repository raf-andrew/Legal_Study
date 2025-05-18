<?php

namespace Tests\Mcp\Core;

use Tests\TestCase;
use Mcp\Core\FailureTracker;
use Illuminate\Support\Facades\File;
use Illuminate\Support\Facades\Log;
use Carbon\Carbon;

class FailureTrackerTest extends TestCase
{
    protected FailureTracker $tracker;
    protected string $failureDir;
    protected string $errorDir;
    protected string $reportDir;

    protected function setUp(): void
    {
        parent::setUp();
        
        $this->failureDir = storage_path('.failures');
        $this->errorDir = storage_path('.errors');
        $this->reportDir = storage_path('failure-reports');
        
        File::makeDirectory($this->failureDir, 0755, true, true);
        File::makeDirectory($this->errorDir, 0755, true, true);
        File::makeDirectory($this->reportDir, 0755, true, true);
        
        $this->tracker = new FailureTracker();
    }

    protected function tearDown(): void
    {
        File::deleteDirectory($this->failureDir);
        File::deleteDirectory($this->errorDir);
        File::deleteDirectory($this->reportDir);
        
        parent::tearDown();
    }

    public function test_failure_tracking(): void
    {
        $testName = 'TestClass::testMethod';
        $message = 'Test failure message';
        $context = ['key' => 'value'];
        
        $this->tracker->trackFailure($testName, $message, $context);
        
        $failureFiles = File::files($this->failureDir);
        $this->assertCount(1, $failureFiles);
        
        $failureContent = File::get($failureFiles[0]);
        $this->assertStringContainsString($testName, $failureContent);
        $this->assertStringContainsString($message, $failureContent);
        $this->assertStringContainsString(json_encode($context), $failureContent);
    }

    public function test_error_tracking(): void
    {
        $testName = 'TestClass::testMethod';
        $message = 'Test error message';
        $context = ['key' => 'value'];
        
        $this->tracker->trackError($testName, $message, $context);
        
        $errorFiles = File::files($this->errorDir);
        $this->assertCount(1, $errorFiles);
        
        $errorContent = File::get($errorFiles[0]);
        $this->assertStringContainsString($testName, $errorContent);
        $this->assertStringContainsString($message, $errorContent);
        $this->assertStringContainsString(json_encode($context), $errorContent);
    }

    public function test_failure_analysis(): void
    {
        $testName = 'TestClass::testMethod';
        $message = 'Test failure message';
        
        $this->tracker->trackFailure($testName, $message);
        $this->tracker->trackFailure($testName, $message);
        
        $analysis = $this->tracker->analyzeFailures();
        
        $this->assertEquals(2, $analysis['total_failures']);
        $this->assertArrayHasKey($testName, $analysis['failure_patterns']);
        $this->assertEquals(2, $analysis['failure_patterns'][$testName]['count']);
        $this->assertCount(1, $analysis['failure_patterns'][$testName]['messages']);
    }

    public function test_error_analysis(): void
    {
        $testName = 'TestClass::testMethod';
        $message = 'Test error message';
        
        $this->tracker->trackError($testName, $message);
        $this->tracker->trackError($testName, $message);
        
        $analysis = $this->tracker->analyzeFailures();
        
        $this->assertEquals(2, $analysis['total_errors']);
        $this->assertArrayHasKey($testName, $analysis['error_patterns']);
        $this->assertEquals(2, $analysis['error_patterns'][$testName]['count']);
        $this->assertCount(1, $analysis['error_patterns'][$testName]['messages']);
    }

    public function test_report_generation(): void
    {
        $testName = 'TestClass::testMethod';
        $message = 'Test failure message';
        
        $this->tracker->trackFailure($testName, $message);
        $reportPath = $this->tracker->generateReport();
        
        $this->assertFileExists($reportPath);
        
        $report = json_decode(File::get($reportPath), true);
        $this->assertIsArray($report);
        $this->assertEquals(1, $report['total_failures']);
        $this->assertArrayHasKey($testName, $report['failure_patterns']);
    }

    public function test_test_history(): void
    {
        $testName = 'TestClass::testMethod';
        $failureMessage = 'Test failure message';
        $errorMessage = 'Test error message';
        
        $this->tracker->trackFailure($testName, $failureMessage);
        $this->tracker->trackError($testName, $errorMessage);
        
        $history = $this->tracker->getTestHistory($testName);
        
        $this->assertCount(1, $history['failures']);
        $this->assertCount(1, $history['errors']);
        $this->assertEquals($failureMessage, $history['failures'][0]['message']);
        $this->assertEquals($errorMessage, $history['errors'][0]['message']);
    }

    public function test_log_cleanup(): void
    {
        $testName = 'TestClass::testMethod';
        $message = 'Test message';
        
        // Create old log files
        $oldTimestamp = now()->subDays(31)->format('Y-m-d_H-i-s');
        File::put($this->failureDir . "/failure_{$oldTimestamp}.log", 'Old failure');
        File::put($this->errorDir . "/error_{$oldTimestamp}.log", 'Old error');
        
        // Create recent log files
        $this->tracker->trackFailure($testName, $message);
        $this->tracker->trackError($testName, $message);
        
        $this->tracker->cleanupOldLogs(30);
        
        $failureFiles = File::files($this->failureDir);
        $errorFiles = File::files($this->errorDir);
        
        $this->assertCount(1, $failureFiles);
        $this->assertCount(1, $errorFiles);
    }
} 