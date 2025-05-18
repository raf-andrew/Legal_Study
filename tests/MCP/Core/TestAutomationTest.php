<?php

namespace Tests\Mcp\Core;

use Tests\TestCase;
use Mcp\Core\TestAutomation;
use Illuminate\Support\Facades\File;
use Illuminate\Support\Facades\Log;
use PHPUnit\Framework\TestResult;
use PHPUnit\Framework\TestFailure;
use PHPUnit\Framework\TestError;

class TestAutomationTest extends TestCase
{
    protected TestAutomation $automation;
    protected string $testDir;
    protected string $reportDir;
    protected string $errorDir;
    protected string $failureDir;

    protected function setUp(): void
    {
        parent::setUp();
        
        $this->testDir = base_path('tests');
        $this->reportDir = storage_path('test-reports');
        $this->errorDir = storage_path('.errors');
        $this->failureDir = storage_path('.failures');
        
        File::makeDirectory($this->reportDir, 0755, true, true);
        File::makeDirectory($this->errorDir, 0755, true, true);
        File::makeDirectory($this->failureDir, 0755, true, true);
        
        $this->automation = new TestAutomation();
    }

    protected function tearDown(): void
    {
        File::deleteDirectory($this->reportDir);
        File::deleteDirectory($this->errorDir);
        File::deleteDirectory($this->failureDir);
        
        parent::tearDown();
    }

    public function test_test_discovery(): void
    {
        $this->automation->runAllTests();
        
        $reportFiles = File::files($this->reportDir);
        $this->assertNotEmpty($reportFiles);
        
        $report = json_decode(File::get($reportFiles[0]), true);
        $this->assertIsArray($report);
        $this->assertArrayHasKey('total', $report);
        $this->assertArrayHasKey('passed', $report);
        $this->assertArrayHasKey('failed', $report);
        $this->assertArrayHasKey('errors', $report);
    }

    public function test_failure_logging(): void
    {
        $failure = new TestFailure(
            'TestClass::testMethod',
            new \Exception('Test failure message')
        );
        
        $this->automation->runAllTests();
        
        $failureFiles = File::files($this->failureDir);
        $this->assertNotEmpty($failureFiles);
        
        $failureContent = File::get($failureFiles[0]);
        $this->assertStringContainsString('Test failure message', $failureContent);
    }

    public function test_error_logging(): void
    {
        $error = new TestError(
            'TestClass::testMethod',
            new \Exception('Test error message')
        );
        
        $this->automation->runAllTests();
        
        $errorFiles = File::files($this->errorDir);
        $this->assertNotEmpty($errorFiles);
        
        $errorContent = File::get($errorFiles[0]);
        $this->assertStringContainsString('Test error message', $errorContent);
    }

    public function test_report_generation(): void
    {
        $result = new TestResult();
        $result->startTest($this);
        $result->endTest($this, 0.1);
        
        $this->automation->runAllTests();
        
        $reportFiles = File::files($this->reportDir);
        $this->assertNotEmpty($reportFiles);
        
        $report = json_decode(File::get($reportFiles[0]), true);
        $this->assertIsArray($report);
        $this->assertArrayHasKey('timestamp', $report);
        $this->assertArrayHasKey('total', $report);
        $this->assertArrayHasKey('passed', $report);
        $this->assertArrayHasKey('failed', $report);
        $this->assertArrayHasKey('errors', $report);
        $this->assertArrayHasKey('duration', $report);
        $this->assertArrayHasKey('memory', $report);
    }

    public function test_result_formatting(): void
    {
        $result = new TestResult();
        $result->startTest($this);
        $result->endTest($this, 0.1);
        
        $formatted = $this->automation->runAllTests();
        
        $this->assertIsArray($formatted);
        $this->assertArrayHasKey('total', $formatted);
        $this->assertArrayHasKey('passed', $formatted);
        $this->assertArrayHasKey('failed', $formatted);
        $this->assertArrayHasKey('errors', $formatted);
        $this->assertArrayHasKey('duration', $formatted);
        $this->assertArrayHasKey('memory', $formatted);
    }
} 