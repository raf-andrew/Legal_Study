#!/bin/bash

# Stop services
echo "Stopping services..."
docker-compose down

# Remove volumes
echo "Removing volumes..."
docker volume rm $(docker volume ls -q | grep -E "legal_study_(postgres|redis|rabbitmq|prometheus)_data") || true

echo "All services stopped!"
