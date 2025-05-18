# Stop services
Write-Host "Stopping services..."
docker-compose down

# Remove volumes
Write-Host "Removing volumes..."
$volumes = docker volume ls --quiet | Select-String -Pattern "legal_study_(postgres|redis|rabbitmq|prometheus)_data"
if ($volumes) {
    docker volume rm $volumes
}

Write-Host "All services stopped!"
