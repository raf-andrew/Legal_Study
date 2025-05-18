#!/bin/bash

# Wait for MySQL to be ready
echo "Waiting for MySQL to be ready..."
while ! mysqladmin ping -h"codespaces-mysql" -u"root" -p"secret" --silent; do
    sleep 1
done
echo "MySQL is ready!"

# Wait for Redis to be ready
echo "Waiting for Redis to be ready..."
while ! redis-cli -h codespaces-redis ping; do
    sleep 1
done
echo "Redis is ready!"

# Run deployment tests
echo "Running deployment tests..."
python .setup/scripts/deployment_test.py

# Start the application
echo "Starting application..."
exec "$@"
