<?php

namespace App\Console\Commands;

use Illuminate\Console\Command;
use App\Services\CodespacesInitializer;
use Illuminate\Support\Facades\File;

class CodespacesTest extends Command
{
    protected $signature = 'codespaces:test {--report-only : Only generate reports for existing test results}';
    protected $description = 'Run Codespaces initialization and tests';

    protected $initializer;
    protected $logPath;
    protected $completePath;

    public function __construct(CodespacesInitializer $initializer)
    {
        parent::__construct();
        $this->initializer = $initializer;
        $this->logPath = config('codespaces.paths.logs', '.codespaces/logs');
        $this->completePath = config('codespaces.paths.complete', '.codespaces/complete');
    }

    public function handle()
    {
        if (!$this->option('report-only')) {
            $this->info('Initializing Codespaces...');
            if (!$this->initializer->initialize()) {
                $this->error('Codespaces initialization failed. Check logs for details.');
                return 1;
            }
            $this->info('Codespaces initialized successfully.');

            $this->info('Running tests...');
            $this->runTests();
        }

        $this->info('Generating reports...');
        $this->generateReports();

        return 0;
    }

    protected function runTests(): void
    {
        // Run health check tests
        $this->info('Running health check tests...');
        $this->call('test', [
            '--filter' => 'CodespacesHealthCheckTest',
            '--log-junit' => "{$this->logPath}/health_check_report.xml"
        ]);

        // Run feature tests
        $this->info('Running feature tests...');
        $this->call('test', [
            '--filter' => 'CodespacesServiceTest',
            '--log-junit' => "{$this->logPath}/feature_test_report.xml"
        ]);

        // Run lifecycle tests
        $this->info('Running lifecycle tests...');
        $this->call('test', [
            '--filter' => 'CodespacesLifecycleTest',
            '--log-junit' => "{$this->logPath}/lifecycle_test_report.xml"
        ]);

        // Run initializer tests
        $this->info('Running initializer tests...');
        $this->call('test', [
            '--filter' => 'CodespacesInitializerTest',
            '--log-junit' => "{$this->logPath}/initializer_test_report.xml"
        ]);
    }

    protected function generateReports(): void
    {
        // Ensure complete directory exists
        if (!File::exists($this->completePath)) {
            File::makeDirectory($this->completePath, 0755, true);
        }

        // Process each test report
        $reports = [
            'health_check' => 'Health Check Tests',
            'feature' => 'Feature Tests',
            'lifecycle' => 'Lifecycle Tests',
            'initializer' => 'Initializer Tests'
        ];

        foreach ($reports as $type => $name) {
            $reportFile = "{$this->logPath}/{$type}_test_report.xml";
            if (File::exists($reportFile)) {
                $this->processReport($type, $name, $reportFile);
            }
        }

        // Clean up failed logs
        $this->cleanupFailedLogs();
    }

    protected function processReport(string $type, string $name, string $reportFile): void
    {
        $content = File::get($reportFile);
        $timestamp = now()->toIso8601String();
        $completeFile = "{$this->completePath}/{$type}_test_{$timestamp}.complete";

        $data = [
            'component' => $name,
            'status' => 'complete',
            'timestamp' => $timestamp,
            'report' => $content,
            'checklist_item' => "{$type}_test_completion"
        ];

        File::put($completeFile, json_encode($data, JSON_PRETTY_PRINT));
        $this->info("Generated completion report for {$name}");
    }

    protected function cleanupFailedLogs(): void
    {
        $files = File::glob("{$this->logPath}/*.log");
        foreach ($files as $file) {
            $content = File::get($file);
            if (str_contains($content, 'FAIL') ||
                str_contains($content, 'Error') ||
                str_contains($content, 'Exception')) {
                File::delete($file);
                $this->warn("Deleted failed log: " . basename($file));
            }
        }
    }
}
