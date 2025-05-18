<?php

require __DIR__ . '/../../../vendor/autoload.php';

use Illuminate\Foundation\Application;
use Illuminate\Support\Facades\File;
use Illuminate\Support\Carbon;
use SebastianBergmann\CodeCoverage\CodeCoverage;
use SebastianBergmann\CodeCoverage\Driver\Selector;
use SebastianBergmann\CodeCoverage\Filter;

class TestExecutor
{
    protected $app;
    protected $reportsPath;
    protected $checklistsPath;
    protected $testResults = [];
    protected $startTime;
    protected $coverage;

    public function __construct()
    {
        $this->app = new Application(
            realpath(__DIR__ . '/../../../')
        );
        $this->reportsPath = base_path('.codespaces/routes/tests/reports');
        $this->checklistsPath = base_path('.codespaces/routes/tests/checklists');
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

    public function execute()
    {
        $this->info('Starting test execution...');
        $this->createDirectories();

        // Get all test classes
        $testClasses = $this->getTestClasses();

        foreach ($testClasses as $testClass) {
            $this->executeTestClass($testClass);
        }

        $this->generateMasterReport();
        $this->updateChecklists();
        $this->displayResults();
    }

    protected function createDirectories()
    {
        if (!File::exists($this->reportsPath)) {
            File::makeDirectory($this->reportsPath, 0755, true);
        }
    }

    protected function getTestClasses()
    {
        $testFiles = File::glob(base_path('.codespaces/routes/tests/Feature/*.php'));
        $testClasses = [];

        foreach ($testFiles as $file) {
            $className = 'Tests\\Feature\\' . pathinfo($file, PATHINFO_FILENAME);
            if (class_exists($className)) {
                $testClasses[] = $className;
            }
        }

        return $testClasses;
    }

    protected function executeTestClass($className)
    {
        $this->info("Executing tests in {$className}...");

        $testClass = new $className();
        $results = [
            'class' => $className,
            'tests' => [],
            'start_time' => Carbon::now()->toIso8601String(),
            'end_time' => null,
            'status' => 'pending',
            'coverage' => 0,
            'errors' => [],
            'failures' => []
        ];

        try {
            // Start coverage collection
            $this->coverage->start($className);

            // Get all test methods
            $methods = get_class_methods($testClass);
            $testMethods = array_filter($methods, function($method) {
                return strpos($method, 'test_') === 0;
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

            // Stop coverage collection
            $this->coverage->stop();

            // Calculate overall status
            if (empty($results['errors']) && empty($results['failures'])) {
                $results['status'] = 'success';
            } elseif (!empty($results['errors'])) {
                $results['status'] = 'error';
            } else {
                $results['status'] = 'failed';
            }

            // Add coverage data
            $results['coverage'] = $this->getCoverageData($className);

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
        $this->testResults[$className] = $results;

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
            'coverage' => []
        ];

        try {
            $startTime = microtime(true);
            $testClass->$method();
            $result['status'] = 'success';

            // Get test coverage data
            if (method_exists($testClass, 'getCoverageData')) {
                $result['coverage'] = $testClass->getCoverageData()[$method] ?? [];
            }
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

    protected function getCoverageData($className)
    {
        $report = $this->coverage->getReport();
        $data = [
            'lines' => $report->getNumExecutedLines(),
            'total' => $report->getNumExecutableLines(),
            'percentage' => $report->getNumExecutedLines() /
                          max(1, $report->getNumExecutableLines()) * 100,
            'files' => []
        ];

        foreach ($report->getFiles() as $file) {
            $data['files'][] = [
                'name' => $file->getPath(),
                'lines' => $file->getNumExecutedLines(),
                'total' => $file->getNumExecutableLines(),
                'percentage' => $file->getNumExecutedLines() /
                              max(1, $file->getNumExecutableLines()) * 100
            ];
        }

        return $data;
    }

    protected function generateReport($results)
    {
        $reportFile = $this->reportsPath . '/' .
                     str_replace('\\', '_', $results['class']) . '_' .
                     Carbon::now()->format('Ymd_His') . '.json';

        File::put($reportFile, json_encode($results, JSON_PRETTY_PRINT));
        return $reportFile;
    }

    protected function updateChecklists()
    {
        $checklistFiles = File::glob($this->checklistsPath . '/*.md');

        foreach ($checklistFiles as $checklistFile) {
            $this->updateChecklist($checklistFile);
        }
    }

    protected function updateChecklist($checklistFile)
    {
        $content = File::get($checklistFile);
        $className = $this->getTestClassFromChecklist($content);

        if (isset($this->testResults[$className])) {
            $results = $this->testResults[$className];
            $reportFile = basename($this->generateReport($results));

            // Update checklist with test results
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
                $testName = ucwords(str_replace('_', ' ', substr($test['name'], 5)));

                $content = preg_replace(
                    "/- \[ \] {$testName}/",
                    "- [$testStatus] {$testName}",
                    $content
                );
            }

            File::put($checklistFile, $content);
        }
    }

    protected function getTestClassFromChecklist($content)
    {
        if (preg_match('/Feature Test Class: `([^`]+)`/', $content, $matches)) {
            return 'Tests\\Feature\\' . $matches[1];
        }
        return null;
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

        $reportFile = $this->reportsPath . '/master_report_' .
                     Carbon::now()->format('Ymd_His') . '.json';

        File::put($reportFile, json_encode($masterReport, JSON_PRETTY_PRINT));
    }

    protected function displayResults()
    {
        $this->info("\nTest Execution Results:");
        $this->line('----------------------------------------');

        foreach ($this->testResults as $className => $result) {
            $status = $result['status'] === 'success' ? '✓' : '✗';
            $this->line("{$status} {$className}: {$result['status']}");

            if (!empty($result['failures'])) {
                $this->error('  Failures:');
                foreach ($result['failures'] as $failure) {
                    $this->line("    - {$failure['name']}: {$failure['message']}");
                }
            }

            if (!empty($result['errors'])) {
                $this->error('  Errors:');
                foreach ($result['errors'] as $error) {
                    $this->line("    - {$error['message']}");
                }
            }

            // Display coverage information
            $coverage = $result['coverage'];
            $coverageStatus = $coverage['percentage'] >= 100 ? '✓' : '✗';
            $this->line("  Coverage: {$coverageStatus} {$coverage['percentage']}%");
        }

        $this->line('----------------------------------------');
        $this->info("Total Duration: " .
                   $this->startTime->diffInSeconds(Carbon::now()) . " seconds");
    }

    protected function info($message)
    {
        echo "\033[32m{$message}\033[0m\n";
    }

    protected function error($message)
    {
        echo "\033[31m{$message}\033[0m\n";
    }

    protected function line($message)
    {
        echo "{$message}\n";
    }
}

// Execute tests
$executor = new TestExecutor();
$executor->execute();
