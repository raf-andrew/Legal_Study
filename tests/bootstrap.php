<?php

require_once __DIR__ . '/../vendor/autoload.php';

// Set up test environment
putenv('APP_ENV=testing');

// Ensure error reporting is set correctly
error_reporting(E_ALL);
ini_set('display_errors', '1'); 