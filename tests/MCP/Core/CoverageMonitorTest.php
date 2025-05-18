<?php

namespace Tests\Mcp\Core;

use Tests\TestCase;
use Mcp\Core\CoverageMonitor;
use Illuminate\Support\Facades\File;
use Illuminate\Support\Facades\Log;

class CoverageMonitorTest extends TestCase
{
    protected CoverageMonitor $monitor;
    protected string $coverageDir;
    protected string $errorDir;
    protected string $failureDir;

    protected function setUp(): void
    {
        parent::setUp();
        
        $this->coverageDir = storage_path('coverage');
        $this->errorDir = storage_path('.errors');
        $this->failureDir = storage_path('.failures');
        
        File::makeDirectory($this->coverageDir, 0755, true, true);
        File::makeDirectory($this->errorDir, 0755, true, true);
        File::makeDirectory($this->failureDir, 0755, true, true);
        
        $this->monitor = new CoverageMonitor();
    }

    protected function tearDown(): void
    {
        File::deleteDirectory($this->coverageDir);
        File::deleteDirectory($this->errorDir);
        File::deleteDirectory($this->failureDir);
        
        parent::tearDown();
    }

    public function test_coverage_report_generation(): void
    {
        $report = $this->monitor->generateCoverageReport();
        
        $this->assertFileExists($this->coverageDir . '/coverage.xml');
        $this->assertFileExists($this->coverageDir . '/index.html');
        $this->assertFileExists($this->coverageDir . '/clover.xml');
        
        $this->assertGreaterThan(0, $report['total']);
        $this->assertGreaterThan(0, $report['covered']);
        $this->assertGreaterThan(0, $report['percentage']);
    }

    public function test_error_logging(): void
    {
        $error = new \Exception('Test error');
        $this->monitor->logError($error);
        
        $errorFiles = File::files($this->errorDir);
        $this->assertCount(1, $errorFiles);
        
        $errorContent = File::get($errorFiles[0]);
        $this->assertStringContainsString('Test error', $errorContent);
    }

    public function test_failure_logging(): void
    {
        $failure = new \RuntimeException('Test failure');
        $this->monitor->logFailure($failure);
        
        $failureFiles = File::files($this->failureDir);
        $this->assertCount(1, $failureFiles);
        
        $failureContent = File::get($failureFiles[0]);
        $this->assertStringContainsString('Test failure', $failureContent);
    }

    public function test_coverage_threshold_check(): void
    {
        $threshold = 90;
        $result = $this->monitor->checkCoverageThreshold($threshold);
        
        $this->assertIsBool($result);
        $this->assertTrue($result);
    }

    public function test_coverage_report_cleanup(): void
    {
        $this->monitor->generateCoverageReport();
        $this->monitor->cleanupReports();
        
        $this->assertFileDoesNotExist($this->coverageDir . '/coverage.xml');
        $this->assertFileDoesNotExist($this->coverageDir . '/index.html');
        $this->assertFileDoesNotExist($this->coverageDir . '/clover.xml');
    }
} 