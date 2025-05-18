<?php

namespace Tests\Commands;

use Illuminate\Console\Command;
use Tests\TestExecutor;

class RunRouteTests extends Command
{
    protected $signature = 'test:routes
        {--report-only : Only generate reports without running tests}
        {--coverage-only : Only generate coverage report}
        {--checklist-only : Only update checklists}';

    protected $description = 'Run all route tests and generate reports';

    public function handle()
    {
        $executor = new TestExecutor();

        if ($this->option('report-only')) {
            $this->info('Generating reports only...');
            $executor->generateReports();
        } elseif ($this->option('coverage-only')) {
            $this->info('Generating coverage report only...');
            $this->displayCoverageReport($executor->getOverallCoverage());
        } elseif ($this->option('checklist-only')) {
            $this->info('Updating checklists only...');
            $executor->updateChecklists();
        } else {
            $this->info('Running route tests...');
            $results = $executor->executeTests();

            // Display results
            $this->displayResults($results);
        }

        $this->info('Done!');
    }

    protected function displayResults($results)
    {
        $this->newLine();
        $this->info('Test Results:');
        $this->newLine();

        foreach ($results['results'] as $class => $tests) {
            $this->line("<fg=cyan>{$class}</>");

            foreach ($tests as $test) {
                $status = $test['status'] === 'passed'
                    ? "<fg=green>✓</>"
                    : "<fg=red>✗</>";

                $this->line("  {$status} {$test['name']}");

                if ($test['status'] === 'failed' && $test['failure']) {
                    $this->line("    <fg=red>{$test['failure']}</>");
                }

                $this->line("    Coverage: {$test['coverage']['lines']}%");
            }
        }

        $this->newLine();
        $this->displayMasterReport();
        $this->newLine();
        $this->displayCoverageReport($results['coverage'] ?? null);
    }

    protected function displayMasterReport()
    {
        $reportFile = $this->getLatestReport('master_report_*.json');
        if (!$reportFile) {
            return;
        }

        $report = json_decode(file_get_contents($reportFile), true);

        $this->info('Master Report:');
        $this->newLine();

        $this->line("Total Tests: {$report['summary']['total_tests']}");
        $this->line("Passed: {$report['summary']['total_passed']}");
        $this->line("Failed: {$report['summary']['total_failed']}");

        if (!empty($report['failed_tests'])) {
            $this->newLine();
            $this->error('Failed Tests:');
            foreach ($report['failed_tests'] as $test) {
                $this->line("  - {$test['class']}::{$test['name']}");
                $this->line("    {$test['failure']}");
            }
        }

        if (!empty($report['incomplete_coverage'])) {
            $this->newLine();
            $this->warn('Incomplete Coverage:');
            foreach ($report['incomplete_coverage'] as $test) {
                $this->line("  - {$test['class']}::{$test['name']}");
                $this->line("    Coverage: {$test['coverage']['lines']}%");
            }
        }
    }

    protected function displayCoverageReport($coverage)
    {
        if (!$coverage) {
            return;
        }

        $this->info('Coverage Report:');
        $this->newLine();

        $this->line("Line Coverage: {$coverage['lines']}%");
        $this->line("Branch Coverage: {$coverage['branches']}%");
        $this->line("Function Coverage: {$coverage['functions']}%");
    }

    protected function getLatestReport($pattern)
    {
        $files = glob(base_path('.codespaces/routes/tests/reports/' . $pattern));

        if (empty($files)) {
            return null;
        }

        usort($files, function($a, $b) {
            return filemtime($b) - filemtime($a);
        });

        return $files[0];
    }
}
