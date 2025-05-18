<?php

namespace Tests\Feature;

use Tests\TestCase;
use App\Console\Commands\CodespacesTest;
use App\Services\CodespacesInitializer;
use Illuminate\Support\Facades\Config;
use Illuminate\Support\Facades\File;

class CodespacesTestCommandTest extends TestCase
{
    protected $command;
    protected $initializer;
    protected $logPath;
    protected $completePath;

    protected function setUp(): void
    {
        parent::setUp();

        $this->logPath = Config::get('codespaces.paths.logs', '.codespaces/logs');
        $this->completePath = Config::get('codespaces.paths.complete', '.codespaces/complete');

        $this->initializer = $this->mock(CodespacesInitializer::class);
        $this->command = new CodespacesTest($this->initializer);

        // Ensure directories exist
        if (!File::exists($this->logPath)) {
            File::makeDirectory($this->logPath, 0755, true);
        }
        if (!File::exists($this->completePath)) {
            File::makeDirectory($this->completePath, 0755, true);
        }
    }

    protected function tearDown(): void
    {
        // Clean up test files
        if (File::exists($this->logPath)) {
            File::deleteDirectory($this->logPath);
        }
        if (File::exists($this->completePath)) {
            File::deleteDirectory($this->completePath);
        }

        parent::tearDown();
    }

    public function test_command_runs_initialization()
    {
        // Mock initializer to succeed
        $this->initializer->shouldReceive('initialize')
            ->once()
            ->andReturn(true);

        // Run command
        $this->artisan('codespaces:test')
            ->expectsOutput('Initializing Codespaces...')
            ->expectsOutput('Codespaces initialized successfully.')
            ->expectsOutput('Running tests...')
            ->expectsOutput('Generating reports...')
            ->assertExitCode(0);
    }

    public function test_command_handles_initialization_failure()
    {
        // Mock initializer to fail
        $this->initializer->shouldReceive('initialize')
            ->once()
            ->andReturn(false);

        // Run command
        $this->artisan('codespaces:test')
            ->expectsOutput('Initializing Codespaces...')
            ->expectsOutput('Codespaces initialization failed. Check logs for details.')
            ->assertExitCode(1);
    }

    public function test_command_generates_reports()
    {
        // Create test report files
        $reports = [
            'health_check' => 'Health Check Tests',
            'feature' => 'Feature Tests',
            'lifecycle' => 'Lifecycle Tests',
            'initializer' => 'Initializer Tests'
        ];

        foreach ($reports as $type => $name) {
            $reportFile = "{$this->logPath}/{$type}_test_report.xml";
            File::put($reportFile, "<testsuites><testsuite name='{$name}'></testsuite></testsuites>");
        }

        // Run command in report-only mode
        $this->artisan('codespaces:test --report-only')
            ->expectsOutput('Generating reports...')
            ->assertExitCode(0);

        // Verify completion reports were generated
        foreach ($reports as $type => $name) {
            $files = File::glob("{$this->completePath}/{$type}_test_*.complete");
            $this->assertNotEmpty($files, "No completion report found for {$name}");
        }
    }

    public function test_command_cleans_up_failed_logs()
    {
        // Create test log files
        $failedLog = "{$this->logPath}/failed.log";
        $successLog = "{$this->logPath}/success.log";

        File::put($failedLog, "FAIL: Test failed\nError: Something went wrong\nException: Oops");
        File::put($successLog, "PASS: Test passed\nSUCCESS: Everything is good");

        // Run command in report-only mode
        $this->artisan('codespaces:test --report-only')
            ->expectsOutput('Generating reports...')
            ->assertExitCode(0);

        // Verify failed log was deleted
        $this->assertFalse(File::exists($failedLog), 'Failed log was not deleted');
        $this->assertTrue(File::exists($successLog), 'Success log was incorrectly deleted');
    }
}
