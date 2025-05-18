<?php

require __DIR__ . '/../../vendor/autoload.php';

$app = require_once __DIR__ . '/../../bootstrap/app.php';
$app->make(\Illuminate\Contracts\Console\Kernel::class)->bootstrap();

use Illuminate\Support\Facades\File;
use Illuminate\Support\Facades\Config;

// Get test type from command line argument
$testType = $argv[1] ?? 'Feature';

// Get the latest test report
$reportDir = Config::get('codespaces.paths.complete') . '/test_reports';
$reports = File::glob("{$reportDir}/test_report_*.json");

if (empty($reports)) {
    echo "No test reports found.\n";
    exit(1);
}

// Sort reports by modification time (newest first)
usort($reports, function($a, $b) {
    return File::lastModified($b) - File::lastModified($a);
});

$latestReport = $reports[0];
$results = json_decode(File::get($latestReport), true);

// Verify test completion
$completed = true;
$failures = [];

if (isset($results['tests'])) {
    foreach ($results['tests'] as $test) {
        if ($test['status'] !== 'passed') {
            $completed = false;
            $failures[] = [
                'name' => $test['name'],
                'message' => $test['message'] ?? 'No error message available'
            ];
        }
    }
}

// Output results
if ($completed) {
    echo "All tests completed successfully.\n";
    echo "Report: {$latestReport}\n";
    exit(0);
} else {
    echo "Test completion verification failed.\n";
    echo "Failed tests:\n";
    foreach ($failures as $failure) {
        echo "- {$failure['name']}: {$failure['message']}\n";
    }
    echo "Report: {$latestReport}\n";
    exit(1);
}
