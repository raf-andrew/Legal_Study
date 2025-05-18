<?php

namespace Mcp\Core;

use Illuminate\Support\Facades\File;
use Illuminate\Support\Facades\Log;
use SebastianBergmann\CodeCoverage\CodeCoverage;
use SebastianBergmann\CodeCoverage\Driver\Selector;
use SebastianBergmann\CodeCoverage\Filter;
use SebastianBergmann\CodeCoverage\Report\Html\Facade as HtmlReport;
use SebastianBergmann\CodeCoverage\Report\Clover as CloverReport;
use SebastianBergmann\CodeCoverage\Report\Xml\Facade as XmlReport;

/**
 * CoverageMonitor handles test coverage monitoring and reporting.
 * 
 * This class is responsible for:
 * - Generating coverage reports in multiple formats (HTML, XML, Clover)
 * - Logging errors and failures to appropriate directories
 * - Checking coverage thresholds
 * - Managing coverage report cleanup
 * 
 * @see Tests\Mcp\Core\CoverageMonitorTest
 */
class CoverageMonitor
{
    protected string $coverageDir;
    protected string $errorDir;
    protected string $failureDir;
    protected CodeCoverage $coverage;

    public function __construct()
    {
        $this->coverageDir = storage_path('coverage');
        $this->errorDir = storage_path('.errors');
        $this->failureDir = storage_path('.failures');
        
        $this->initializeCoverage();
    }

    protected function initializeCoverage(): void
    {
        $filter = new Filter();
        $filter->includeDirectory(base_path('src'));
        
        $this->coverage = new CodeCoverage(
            (new Selector())->forLineCoverage($filter),
            $filter
        );
    }

    /**
     * Generates coverage reports in multiple formats.
     * 
     * @return array Coverage statistics
     */
    public function generateCoverageReport(): array
    {
        $this->coverage->start('coverage');
        
        // Collect coverage data
        $this->coverage->stop();
        
        // Generate reports
        (new HtmlReport())->process($this->coverage, $this->coverageDir);
        (new XmlReport())->process($this->coverage, $this->coverageDir . '/coverage.xml');
        (new CloverReport())->process($this->coverage, $this->coverageDir . '/clover.xml');
        
        return [
            'total' => $this->coverage->getReport()->numberOfExecutedLines(),
            'covered' => $this->coverage->getReport()->numberOfExecutedLines(),
            'percentage' => $this->coverage->getReport()->percentageOfExecutedLines()
        ];
    }

    /**
     * Logs an error to the .errors directory.
     * 
     * @param \Throwable $error The error to log
     */
    public function logError(\Throwable $error): void
    {
        $timestamp = now()->format('Y-m-d_H-i-s');
        $filename = "error_{$timestamp}.log";
        
        $content = sprintf(
            "[%s] %s\nFile: %s\nLine: %d\nStack trace:\n%s\n",
            $timestamp,
            $error->getMessage(),
            $error->getFile(),
            $error->getLine(),
            $error->getTraceAsString()
        );
        
        File::put($this->errorDir . '/' . $filename, $content);
        Log::error($error->getMessage(), ['exception' => $error]);
    }

    /**
     * Logs a failure to the .failures directory.
     * 
     * @param \Throwable $failure The failure to log
     */
    public function logFailure(\Throwable $failure): void
    {
        $timestamp = now()->format('Y-m-d_H-i-s');
        $filename = "failure_{$timestamp}.log";
        
        $content = sprintf(
            "[%s] %s\nFile: %s\nLine: %d\nStack trace:\n%s\n",
            $timestamp,
            $failure->getMessage(),
            $failure->getFile(),
            $failure->getLine(),
            $failure->getTraceAsString()
        );
        
        File::put($this->failureDir . '/' . $filename, $content);
        Log::error($failure->getMessage(), ['exception' => $failure]);
    }

    /**
     * Checks if the current coverage meets the specified threshold.
     * 
     * @param int $threshold The minimum coverage percentage required
     * @return bool True if coverage meets or exceeds the threshold
     */
    public function checkCoverageThreshold(int $threshold): bool
    {
        $report = $this->coverage->getReport();
        $percentage = $report->percentageOfExecutedLines();
        
        return $percentage >= $threshold;
    }

    /**
     * Cleans up coverage reports.
     */
    public function cleanupReports(): void
    {
        File::deleteDirectory($this->coverageDir);
    }
} 