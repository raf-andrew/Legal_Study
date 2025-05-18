<?php

require_once __DIR__ . '/vendor/autoload.php';

use LegalStudy\Console\Application;
use LegalStudy\Console\Commands\TestCommand;
use LegalStudy\Console\Commands\HealthCheckCommand;

$app = new Application([
    'name' => 'Legal Study System Console',
    'version' => '1.0.0'
]);

// Register commands
$app->registerCommand(new TestCommand());
$app->registerCommand(new HealthCheckCommand());

// Run the application
exit($app->run($argv)); 