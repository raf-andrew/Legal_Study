#!/bin/bash

# Set Xdebug mode for coverage
export XDEBUG_MODE=coverage

# Run PHPUnit with coverage
vendor/bin/phpunit "$@" 