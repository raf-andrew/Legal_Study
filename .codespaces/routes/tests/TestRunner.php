<?php

namespace App\Tests;

use Illuminate\Support\Facades\File;
use Illuminate\Support\Carbon;
use Illuminate\Support\Str;
use SebastianBergmann\CodeCoverage\CodeCoverage;
use SebastianBergmann\CodeCoverage\Driver\Selector;
use SebastianBergmann\CodeCoverage\Filter;

class TestRunner
{
    protected $reportPath;
    protected $checklistPath;
    protected $testResults = [];
    protected $startTime;
    protected $coverage;

    public function __construct()
    {
        $this->reportPath = base_path('.codespaces/routes/tests/reports');
        $this->checklistPath = base_path('.codespaces/routes/tests/checklists');
        $this->startTime = Carbon::now();
        $this->initializeCoverage();
    }

    protected function initializeCoverage()
    {
        $filter = new Filter();
        $filter->includeDirectory(base_path('app'));
        $filter->includeDirectory(base_path('routes'));

        $this->coverage = new CodeCoverage(
            (new Selector)->forLineCoverage($filter),
            $filter
        );
    }

    public function runTests()
    {
        // Create reports directory if it doesn't exist
        if (!File::exists($this->reportPath)) {
            File::makeDirectory($this->reportPath, 0755, true);
        }

        // Start coverage collection
        $this->coverage->start('test_suite');

        // Run User Profile Tests
        $this->runUserProfileTests();

        // Run Health Check Tests
        $this->runHealthCheckTests();

        // Stop coverage collection
        $this->coverage->stop();

        // Generate coverage report
        $this->generateCoverageReport();

        // Generate master report
        $this->generateMasterReport();
    }

    protected function runUserProfileTests()
    {
        $testClass = new \Tests\Feature\UserProfileTest();
        $results = $this->executeTestClass($testClass);
        $this->testResults['user_profile'] = $results;
        $this->updateChecklist('user_profile_checklist.md', $results);
    }

    protected function runHealthCheckTests()
    {
        $testClass = new \Tests\Feature\HealthCheckTest();
        $results = $this->executeTestClass($testClass);
        $this->testResults['health_check'] = $results;
        $this->updateChecklist('health_check_checklist.md', $results);
    }

    protected function executeTestClass($testClass)
    {
        $results = [
            'class' => get_class($testClass),
            'tests' => [],
            'start_time' => Carbon::now()->toIso8601String(),
            'end_time' => null,
            'status' => 'pending',
            'coverage' => 0,
            'errors' => [],
            'failures' => []
        ];

        try {
            // Get all test methods
            $methods = get_class_methods($testClass);
            $testMethods = array_filter($methods, function($method) {
                return Str::startsWith($method, 'test_') ||
                       (new \ReflectionMethod($testClass, $method))->getDocComment() === '/** @test */';
            });

            foreach ($testMethods as $method) {
                $testResult = $this->executeTestMethod($testClass, $method);
                $results['tests'][] = $testResult;

                if ($testResult['status'] === 'failed') {
                    $results['failures'][] = $testResult;
                } elseif ($testResult['status'] === 'error') {
                    $results['errors'][] = $testResult;
                }
            }

            // Calculate overall status
            if (empty($results['errors']) && empty($results['failures'])) {
                $results['status'] = 'success';
            } elseif (!empty($results['errors'])) {
                $results['status'] = 'error';
            } else {
                $results['status'] = 'failed';
            }

        } catch (\Exception $e) {
            $results['status'] = 'error';
            $results['errors'][] = [
                'message' => $e->getMessage(),
                'trace' => $e->getTraceAsString()
            ];
        }

        $results['end_time'] = Carbon::now()->toIso8601String();
        $results['duration'] = Carbon::parse($results['start_time'])->diffInSeconds($results['end_time']);

        // Generate report
        $this->generateReport($results);

        return $results;
    }

    protected function executeTestMethod($testClass, $method)
    {
        $result = [
            'name' => $method,
            'status' => 'pending',
            'start_time' => Carbon::now()->toIso8601String(),
            'end_time' => null,
            'duration' => 0,
            'message' => null,
            'trace' => null,
            'coverage' => 0
        ];

        try {
            $startTime = microtime(true);
            $testClass->$method();
            $result['status'] = 'success';
        } catch (\PHPUnit\Framework\AssertionFailedError $e) {
            $result['status'] = 'failed';
            $result['message'] = $e->getMessage();
            $result['trace'] = $e->getTraceAsString();
        } catch (\Exception $e) {
            $result['status'] = 'error';
            $result['message'] = $e->getMessage();
            $result['trace'] = $e->getTraceAsString();
        }

        $result['end_time'] = Carbon::now()->toIso8601String();
        $result['duration'] = microtime(true) - $startTime;

        return $result;
    }

    protected function generateReport($results)
    {
        $reportFile = $this->reportPath . '/' . Str::snake($results['class']) . '_' .
                     Carbon::now()->format('Ymd_His') . '.json';

        // Add coverage information
        $results['coverage'] = [
            'lines' => $this->coverage->getReport()->getNumExecutedLines(),
            'total' => $this->coverage->getReport()->getNumExecutableLines(),
            'percentage' => $this->coverage->getReport()->getNumExecutedLines() /
                          max(1, $this->coverage->getReport()->getNumExecutableLines()) * 100
        ];

        File::put($reportFile, json_encode($results, JSON_PRETTY_PRINT));

        return $reportFile;
    }

    protected function updateChecklist($checklistFile, $results)
    {
        $checklistPath = $this->checklistPath . '/' . $checklistFile;
        if (!File::exists($checklistPath)) {
            return;
        }

        $content = File::get($checklistPath);
        $reportFile = basename($this->generateReport($results));

        // Update checklist with test results and coverage
        $status = $results['status'] === 'success' ? 'x' : ' ';
        $coverageStatus = $results['coverage']['percentage'] >= 100 ? 'x' : ' ';

        $content = preg_replace(
            '/- \[ \] Feature Test Class/',
            "- [$status] Feature Test Class\n" .
            "  - Report: [{$reportFile}](mdc:.codespaces/routes/tests/reports/{$reportFile})\n" .
            "  - Coverage: [{$coverageStatus}] {$results['coverage']['percentage']}%\n" .
            "  - Tests: " . count($results['tests']) . " total, " .
            count(array_filter($results['tests'], fn($t) => $t['status'] === 'success')) . " passed",
            $content
        );

        // Update individual test items
        foreach ($results['tests'] as $test) {
            $testStatus = $test['status'] === 'success' ? 'x' : ' ';
            $testName = Str::title(str_replace('_', ' ', $test['name']));

            $content = preg_replace(
                "/- \[ \] {$testName}/",
                "- [$testStatus] {$testName}",
                $content
            );
        }

        File::put($checklistPath, $content);
    }

    protected function generateCoverageReport()
    {
        $coverageReport = [
            'start_time' => $this->startTime->toIso8601String(),
            'end_time' => Carbon::now()->toIso8601String(),
            'duration' => $this->startTime->diffInSeconds(Carbon::now()),
            'coverage' => [
                'lines' => $this->coverage->getReport()->getNumExecutedLines(),
                'total' => $this->coverage->getReport()->getNumExecutableLines(),
                'percentage' => $this->coverage->getReport()->getNumExecutedLines() /
                              max(1, $this->coverage->getReport()->getNumExecutableLines()) * 100
            ],
            'files' => []
        ];

        foreach ($this->coverage->getReport()->getFiles() as $file) {
            $coverageReport['files'][] = [
                'name' => $file->getPath(),
                'lines' => $file->getNumExecutedLines(),
                'total' => $file->getNumExecutableLines(),
                'percentage' => $file->getNumExecutedLines() /
                              max(1, $file->getNumExecutableLines()) * 100
            ];
        }

        $reportFile = $this->reportPath . '/coverage_report_' .
                     Carbon::now()->format('Ymd_His') . '.json';

        File::put($reportFile, json_encode($coverageReport, JSON_PRETTY_PRINT));
    }

    protected function generateMasterReport()
    {
        $masterReport = [
            'start_time' => $this->startTime->toIso8601String(),
            'end_time' => Carbon::now()->toIso8601String(),
            'duration' => $this->startTime->diffInSeconds(Carbon::now()),
            'results' => $this->testResults,
            'status' => 'success',
            'coverage' => [
                'lines' => $this->coverage->getReport()->getNumExecutedLines(),
                'total' => $this->coverage->getReport()->getNumExecutableLines(),
                'percentage' => $this->coverage->getReport()->getNumExecutedLines() /
                              max(1, $this->coverage->getReport()->getNumExecutableLines()) * 100
            ]
        ];

        // Check overall status
        foreach ($this->testResults as $result) {
            if ($result['status'] !== 'success') {
                $masterReport['status'] = $result['status'];
                break;
            }
        }

        $reportFile = $this->reportPath . '/master_report_' .
                     Carbon::now()->format('Ymd_His') . '.json';

        File::put($reportFile, json_encode($masterReport, JSON_PRETTY_PRINT));
    }
}
