<?php

namespace App\Tests\Commands;

use Illuminate\Console\Command;
use App\Tests\TestExecutor;

class RunTests extends Command
{
    protected $signature = 'test:execute
        {--report-only : Only generate reports without running tests}
        {--checklist-only : Only update checklists}';

    protected $description = 'Execute all route tests and generate reports';

    public function handle()
    {
        $this->info('Starting test execution...');

        if ($this->option('report-only')) {
            $this->info('Report-only mode: Skipping test execution');
            return;
        }

        if ($this->option('checklist-only')) {
            $this->info('Checklist-only mode: Updating checklists');
            return;
        }

        $executor = new TestExecutor();
        $executor->execute();
    }
}
