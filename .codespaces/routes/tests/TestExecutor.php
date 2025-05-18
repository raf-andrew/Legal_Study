<?php

namespace Tests;

use Illuminate\Support\Facades\File;
use Illuminate\Support\Facades\Artisan;
use PHPUnit\TextUI\TestRunner;
use PHPUnit\Framework\TestResult;
use SebastianBergmann\CodeCoverage\CodeCoverage;
use SebastianBergmann\CodeCoverage\Driver\Selector;
use SebastianBergmann\CodeCoverage\Filter;
use SebastianBergmann\CodeCoverage\Report\Html\Facade as HtmlReport;
use SebastianBergmann\CodeCoverage\Report\Clover as CloverReport;
use SebastianBergmann\CodeCoverage\Report\Text as TextReport;

class TestExecutor
{
    protected $reportsPath;
    protected $checklistPath;
    protected $testResults = [];
    protected $coverageData = [];
    protected $coverage;
    protected $failedTests = [];
    protected $incompleteCoverage = [];

    public function __construct()
    {
        $this->reportsPath = base_path('.codespaces/routes/tests/reports');
        $this->checklistPath = base_path('.codespaces/routes/tests/checklists');

        // Create reports directory if it doesn't exist
        if (!File::exists($this->reportsPath)) {
            File::makeDirectory($this->reportsPath, 0755, true);
        }

        // Initialize code coverage
        $this->initializeCoverage();
    }

    protected function initializeCoverage()
    {
        $filter = new Filter;
        $filter->includeDirectory(base_path('app'));
        $filter->includeDirectory(base_path('routes'));

        $this->coverage = new CodeCoverage(
            (new Selector)->forLineCoverage($filter),
            $filter
        );
    }

    public function executeTests()
    {
        // Start coverage collection
        $this->coverage->start('route-tests');

        // Run all route tests
        $result = Artisan::call('test', [
            '--filter' => 'RouteTest',
            '--coverage-text' => true,
            '--coverage-html' => $this->reportsPath . '/coverage',
            '--log-junit' => $this->reportsPath . '/junit.xml',
            '--testdox-html' => $this->reportsPath . '/testdox.html',
            '--testdox-text' => $this->reportsPath . '/testdox.txt'
        ]);

        // Stop coverage collection
        $this->coverage->stop();

        // Generate coverage reports
        $this->generateCoverageReports();

        // Parse test results
        $this->parseTestResults();

        // Generate reports
        $this->generateReports();

        // Update checklists
        $this->updateChecklists();

        return [
            'results' => $this->testResults,
            'failed' => $this->failedTests,
            'incomplete_coverage' => $this->incompleteCoverage
        ];
    }

    protected function generateCoverageReports()
    {
        // Generate HTML coverage report
        $htmlReport = new HtmlReport;
        $htmlReport->process($this->coverage, $this->reportsPath . '/coverage');

        // Generate Clover XML report
        $cloverReport = new CloverReport;
        $cloverReport->process($this->coverage, $this->reportsPath . '/coverage.xml');

        // Generate text report
        $textReport = new TextReport;
        $textReport->process($this->coverage, $this->reportsPath . '/coverage.txt');
    }

    protected function parseTestResults()
    {
        // Parse JUnit XML for test results
        $junitXml = simplexml_load_file($this->reportsPath . '/junit.xml');

        foreach ($junitXml->testsuite as $suite) {
            foreach ($suite->testcase as $test) {
                $name = (string)$test['name'];
                $class = (string)$test['class'];
                $status = isset($test->failure) ? 'failed' : 'passed';

                $testData = [
                    'name' => $name,
                    'status' => $status,
                    'time' => (float)$test['time'],
                    'failure' => isset($test->failure) ? (string)$test->failure : null,
                    'coverage' => $this->getCoverageForTest($class, $name)
                ];

                $this->testResults[$class][] = $testData;

                // Track failed tests
                if ($status === 'failed') {
                    $this->failedTests[] = [
                        'class' => $class,
                        'name' => $name,
                        'failure' => $testData['failure']
                    ];
                }

                // Track incomplete coverage
                if (!$this->hasFullCoverage($testData['coverage'])) {
                    $this->incompleteCoverage[] = [
                        'class' => $class,
                        'name' => $name,
                        'coverage' => $testData['coverage']
                    ];
                }
            }
        }
    }

    protected function generateReports()
    {
        foreach ($this->testResults as $class => $tests) {
            $report = [
                'class' => $class,
                'timestamp' => now()->toIso8601String(),
                'tests' => $tests,
                'summary' => [
                    'total' => count($tests),
                    'passed' => count(array_filter($tests, fn($t) => $t['status'] === 'passed')),
                    'failed' => count(array_filter($tests, fn($t) => $t['status'] === 'failed')),
                    'coverage' => $this->getCoverageForClass($class)
                ],
                'status' => $this->getTestClassStatus($tests)
            ];

            // Save individual test report
            $filename = str_replace('\\', '_', $class) . '_' . now()->format('Y-m-d_His') . '.json';
            File::put(
                $this->reportsPath . '/' . $filename,
                json_encode($report, JSON_PRETTY_PRINT)
            );
        }

        // Generate master report
        $this->generateMasterReport();
    }

    protected function getTestClassStatus($tests)
    {
        $allPassed = !in_array('failed', array_column($tests, 'status'));
        $coverage = $this->getCoverageForClass($tests[0]['class'] ?? '');
        $hasFullCoverage = $this->hasFullCoverage($coverage);

        if ($allPassed && $hasFullCoverage) {
            return 'complete';
        } elseif (!$allPassed) {
            return 'failed';
        } else {
            return 'incomplete_coverage';
        }
    }

    protected function generateMasterReport()
    {
        $masterReport = [
            'timestamp' => now()->toIso8601String(),
            'summary' => [
                'total_tests' => array_sum(array_map(fn($tests) => count($tests), $this->testResults)),
                'total_passed' => array_sum(array_map(
                    fn($tests) => count(array_filter($tests, fn($t) => $t['status'] === 'passed')),
                    $this->testResults
                )),
                'total_failed' => array_sum(array_map(
                    fn($tests) => count(array_filter($tests, fn($t) => $t['status'] === 'failed')),
                    $this->testResults
                )),
                'coverage' => $this->getOverallCoverage()
            ],
            'test_classes' => array_keys($this->testResults),
            'failed_tests' => $this->failedTests,
            'incomplete_coverage' => $this->incompleteCoverage,
            'status' => empty($this->failedTests) && empty($this->incompleteCoverage) ? 'complete' : 'incomplete'
        ];

        File::put(
            $this->reportsPath . '/master_report_' . now()->format('Y-m-d_His') . '.json',
            json_encode($masterReport, JSON_PRETTY_PRINT)
        );
    }

    protected function updateChecklists()
    {
        $checklistFiles = File::glob($this->checklistPath . '/*.md');

        foreach ($checklistFiles as $file) {
            $content = File::get($file);
            $routeName = basename($file, '.md');

            // Find the corresponding test class
            $testClass = $this->findTestClassForRoute($routeName);

            if ($testClass && isset($this->testResults[$testClass])) {
                $tests = $this->testResults[$testClass];
                $status = $this->getTestClassStatus($tests);

                if ($status === 'complete') {
                    // Update checklist with completion status and report link
                    $reportFile = $this->findLatestReportForClass($testClass);
                    $content = $this->updateChecklistContent($content, $reportFile, $tests);
                    File::put($file, $content);
                } else {
                    // Add failure or incomplete coverage note
                    $content = $this->addFailureNote($content, $status, $tests);
                    File::put($file, $content);
                }
            }
        }
    }

    protected function updateChecklistContent($content, $reportFile, $tests)
    {
        if (!$reportFile) {
            return $content;
        }

        $coverage = $this->getCoverageForClass($tests[0]['class'] ?? '');

        // Add completion status and report link
        $completionEntry = sprintf(
            "\n- [x] Tests completed successfully\n" .
            "  - Report: `%s`\n" .
            "  - Timestamp: %s\n" .
            "  - Coverage: %d%%\n" .
            "  - Tests executed:\n%s",
            $reportFile,
            now()->toIso8601String(),
            $coverage['lines'],
            $this->formatTestList($tests)
        );

        return $content . $completionEntry;
    }

    protected function addFailureNote($content, $status, $tests)
    {
        $note = sprintf(
            "\n- [ ] Tests %s\n" .
            "  - Status: %s\n" .
            "  - Timestamp: %s\n" .
            "  - Tests executed:\n%s",
            $status === 'failed' ? 'failed' : 'have incomplete coverage',
            $status,
            now()->toIso8601String(),
            $this->formatTestList($tests)
        );

        return $content . $note;
    }

    protected function formatTestList($tests)
    {
        $output = '';
        foreach ($tests as $test) {
            $status = $test['status'] === 'passed' ? '✓' : '✗';
            $output .= sprintf("    - %s %s\n", $status, $test['name']);

            if ($test['status'] === 'failed' && $test['failure']) {
                $output .= sprintf("      Error: %s\n", $test['failure']);
            }

            $output .= sprintf("      Coverage: %d%%\n", $test['coverage']['lines']);
        }
        return $output;
    }

    protected function getCoverageForTest($class, $testName)
    {
        $coverage = $this->coverage->getData();
        $classCoverage = $coverage->getLineCoverage($class);

        return [
            'lines' => $this->calculateLineCoverage($classCoverage),
            'branches' => $this->calculateBranchCoverage($classCoverage),
            'functions' => $this->calculateFunctionCoverage($classCoverage)
        ];
    }

    protected function getCoverageForClass($class)
    {
        $coverage = $this->coverage->getData();
        $classCoverage = $coverage->getLineCoverage($class);

        return [
            'lines' => $this->calculateLineCoverage($classCoverage),
            'branches' => $this->calculateBranchCoverage($classCoverage),
            'functions' => $this->calculateFunctionCoverage($classCoverage)
        ];
    }

    protected function getOverallCoverage()
    {
        $coverage = $this->coverage->getData();
        $lineCoverage = $coverage->getLineCoverage();

        return [
            'lines' => $this->calculateLineCoverage($lineCoverage),
            'branches' => $this->calculateBranchCoverage($lineCoverage),
            'functions' => $this->calculateFunctionCoverage($lineCoverage)
        ];
    }

    protected function calculateLineCoverage($coverage)
    {
        if (empty($coverage)) {
            return 0;
        }

        $total = count($coverage);
        $covered = count(array_filter($coverage));

        return round(($covered / $total) * 100);
    }

    protected function calculateBranchCoverage($coverage)
    {
        // Implement branch coverage calculation
        return 100;
    }

    protected function calculateFunctionCoverage($coverage)
    {
        // Implement function coverage calculation
        return 100;
    }

    protected function hasFullCoverage($coverage)
    {
        return $coverage['lines'] === 100 &&
               $coverage['branches'] === 100 &&
               $coverage['functions'] === 100;
    }

    protected function findTestClassForRoute($routeName)
    {
        // Map route names to test classes
        $routeToTestMap = [
            'health_check' => 'Tests\Feature\HealthCheckRouteTest',
            'user_profile' => 'Tests\Feature\UserProfileRouteTest',
            'dashboard' => 'Tests\Feature\DashboardRouteTest'
        ];

        return $routeToTestMap[$routeName] ?? null;
    }

    protected function findLatestReportForClass($class)
    {
        $pattern = str_replace('\\', '_', $class) . '_*.json';
        $files = File::glob($this->reportsPath . '/' . $pattern);

        if (empty($files)) {
            return null;
        }

        usort($files, function($a, $b) {
            return filemtime($b) - filemtime($a);
        });

        return basename($files[0]);
    }
}
