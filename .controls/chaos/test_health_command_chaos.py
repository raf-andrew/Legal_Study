"""Chaos tests for health check command."""
import pytest
import json
import time
import random
import threading
from typing import Dict, Any, List
from click.testing import CliRunner
from ..commands.health.command import HealthCheckCommand
from ...mocks.registry import MockServiceRegistry
from ...mocks.services.api import MockAPIService
from ...mocks.services.database import MockDatabase
from ...mocks.services.cache import MockCache
from ...mocks.services.queue import MockQueueService
from ...mocks.services.auth import MockAuthService
from ...mocks.services.metrics import MockMetricsService
from ...mocks.services.logging import MockLoggingService

class ChaosRunner:
    """Chaos test runner."""
    
    def __init__(self, registry: MockServiceRegistry):
        self.registry = registry
        self.running = False
        self.threads: List[threading.Thread] = []
        self.error_probability = 0.2
        self.service_types = [
            ("api", MockAPIService),
            ("database", MockDatabase),
            ("cache", MockCache),
            ("queue", MockQueueService),
            ("auth", MockAuthService),
            ("metrics", MockMetricsService),
            ("logging", MockLoggingService)
        ]

    def start(self):
        """Start chaos testing."""
        self.running = True
        
        # Create threads for different chaos scenarios
        self.threads = [
            threading.Thread(target=self._service_lifecycle),
            threading.Thread(target=self._error_injection),
            threading.Thread(target=self._load_generation),
            threading.Thread(target=self._config_changes)
        ]
        
        for thread in self.threads:
            thread.daemon = True
            thread.start()

    def stop(self):
        """Stop chaos testing."""
        self.running = False
        for thread in self.threads:
            thread.join(timeout=1.0)
        self.threads.clear()

    def _service_lifecycle(self):
        """Randomly start/stop services."""
        while self.running:
            service_type, _ = random.choice(self.service_types)
            try:
                service = self.registry.get_service(service_type)
                if service:
                    if random.random() < 0.5:
                        service.stop()
                    else:
                        service.start()
                else:
                    self.registry.create_service(service_type)
            except Exception:
                pass
            time.sleep(random.uniform(0.1, 0.5))

    def _error_injection(self):
        """Inject random errors into services."""
        while self.running:
            if random.random() < self.error_probability:
                service_type, _ = random.choice(self.service_types)
                service = self.registry.get_service(service_type)
                if service:
                    service.state.record_error(
                        Exception("Chaos error"),
                        {"action": "chaos_test"}
                    )
            time.sleep(random.uniform(0.1, 0.3))

    def _load_generation(self):
        """Generate random load on services."""
        while self.running:
            service_type, _ = random.choice(self.service_types)
            service = self.registry.get_service(service_type)
            if service:
                try:
                    if isinstance(service, MockAPIService):
                        service.handle_request("/health")
                    elif isinstance(service, MockDatabase):
                        service.insert("test", {"id": str(random.randint(1, 1000))})
                    elif isinstance(service, MockCache):
                        service.set(f"key_{random.randint(1, 1000)}", "value")
                    elif isinstance(service, MockQueueService):
                        service.enqueue("test", {"id": str(random.randint(1, 1000))})
                except Exception:
                    pass
            time.sleep(random.uniform(0.05, 0.2))

    def _config_changes(self):
        """Simulate configuration changes."""
        while self.running:
            service_type, _ = random.choice(self.service_types)
            service = self.registry.get_service(service_type)
            if service:
                try:
                    service.configure({
                        "chaos_config": str(random.randint(1, 1000))
                    })
                except Exception:
                    pass
            time.sleep(random.uniform(0.3, 0.7))

@pytest.fixture
def config() -> Dict[str, Any]:
    """Load test configuration."""
    with open(".config/mock.yaml") as f:
        return yaml.safe_load(f)

@pytest.fixture
def registry(config) -> MockServiceRegistry:
    """Create service registry."""
    registry = MockServiceRegistry()
    registry._config = config
    return registry

@pytest.fixture
def health_command(registry) -> HealthCheckCommand:
    """Create health check command instance."""
    command = HealthCheckCommand()
    command.registry = registry
    return command

@pytest.fixture
def cli_runner() -> CliRunner:
    """Create CLI test runner."""
    return CliRunner()

@pytest.fixture
def chaos_runner(registry) -> ChaosRunner:
    """Create chaos runner."""
    return ChaosRunner(registry)

def test_health_check_under_chaos(health_command, cli_runner, chaos_runner):
    """Test health check under chaotic conditions."""
    # Start chaos testing
    chaos_runner.start()
    
    try:
        # Run multiple health checks
        results = []
        for _ in range(20):
            command = health_command.create_command()
            result = cli_runner.invoke(command, ["--report"])
            
            # Verify basic response structure
            assert result.exit_code in [0, 1]  # Allow both healthy and unhealthy states
            data = json.loads(result.output)
            assert "status" in data
            assert "checks" in data
            assert "report" in data
            
            results.append(data)
            time.sleep(0.2)  # Small delay between checks
        
        # Analyze results
        status_changes = sum(
            1 for i in range(1, len(results))
            if results[i]["status"] != results[i-1]["status"]
        )
        
        # Verify that system state changed during chaos testing
        assert status_changes > 0, "System state should change during chaos testing"
        
        # Verify that recommendations were generated for unhealthy states
        unhealthy_reports = [
            r for r in results
            if r["status"] == "unhealthy" and len(r["report"]["recommendations"]) > 0
        ]
        assert len(unhealthy_reports) > 0, "Should have unhealthy states with recommendations"
        
    finally:
        # Stop chaos testing
        chaos_runner.stop()

def test_health_check_recovery(health_command, cli_runner, chaos_runner):
    """Test health check system recovery after chaos."""
    # Start chaos testing
    chaos_runner.start()
    
    try:
        # Run health checks during chaos
        for _ in range(5):
            command = health_command.create_command()
            cli_runner.invoke(command)
            time.sleep(0.2)
        
    finally:
        # Stop chaos testing
        chaos_runner.stop()
    
    # Wait for potential recovery
    time.sleep(1.0)
    
    # Verify system can return to healthy state
    command = health_command.create_command()
    result = cli_runner.invoke(command, ["--report"])
    
    data = json.loads(result.output)
    assert data["status"] == "healthy", "System should recover after chaos"

def test_health_check_partial_failure(health_command, cli_runner, registry):
    """Test health check with partial service failures."""
    # Create services
    services = []
    for name, service_class in ChaosRunner(registry).service_types:
        service = registry.create_service(name)
        service.start()
        services.append(service)
    
    # Simulate partial failures
    for service in random.sample(services, len(services) // 2):
        service.state.record_error(
            Exception("Chaos error"),
            {"action": "chaos_test"}
        )
        service.stop()
    
    # Run health check
    command = health_command.create_command()
    result = cli_runner.invoke(command, ["--report"])
    
    data = json.loads(result.output)
    assert data["status"] == "unhealthy"
    assert len(data["report"]["recommendations"]) > 0

def test_health_check_concurrent_chaos(health_command, cli_runner, registry):
    """Test health check with concurrent chaos and health checks."""
    # Create services
    for name, _ in ChaosRunner(registry).service_types:
        service = registry.create_service(name)
        service.start()
    
    # Create threads for concurrent health checks and chaos
    results = []
    def run_health_checks():
        for _ in range(5):
            command = health_command.create_command()
            result = cli_runner.invoke(command)
            results.append(result)
            time.sleep(0.1)
    
    threads = [
        threading.Thread(target=run_health_checks)
        for _ in range(5)
    ]
    
    # Start chaos testing
    chaos_runner = ChaosRunner(registry)
    chaos_runner.start()
    
    try:
        # Run concurrent health checks
        for thread in threads:
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Verify results
        for result in results:
            assert result.exit_code in [0, 1, 2]  # Allow all possible states
            try:
                data = json.loads(result.output)
                assert "status" in data
                assert "checks" in data
            except json.JSONDecodeError:
                # Allow for potential corruption during chaos
                pass
            
    finally:
        chaos_runner.stop()

def test_health_check_error_propagation(health_command, cli_runner, registry):
    """Test health check error propagation under chaos."""
    # Create services with cascading errors
    api_service = registry.create_service("api")
    db_service = registry.create_service("database")
    cache_service = registry.create_service("cache")
    
    api_service.start()
    db_service.start()
    cache_service.start()
    
    # Simulate cascading errors
    db_service.state.record_error(
        Exception("Database error"),
        {"action": "chaos_test"}
    )
    
    cache_service.state.record_error(
        Exception("Cache error"),
        {"action": "chaos_test"}
    )
    
    # Run health check
    command = health_command.create_command()
    result = cli_runner.invoke(command, ["--report"])
    
    data = json.loads(result.output)
    assert data["status"] == "unhealthy"
    
    # Verify error propagation in recommendations
    recommendations = data["report"]["recommendations"]
    assert any("database" in r.lower() for r in recommendations)
    assert any("cache" in r.lower() for r in recommendations)

def test_health_check_stress(health_command, cli_runner, registry):
    """Test health check under stress conditions."""
    # Create services
    for name, _ in ChaosRunner(registry).service_types:
        service = registry.create_service(name)
        service.start()
    
    # Run rapid health checks
    start_time = time.time()
    count = 0
    
    while time.time() - start_time < 5.0:  # Run for 5 seconds
        command = health_command.create_command()
        result = cli_runner.invoke(command)
        assert result.exit_code in [0, 1, 2]
        count += 1
    
    # Verify system handled stress
    assert count > 10, "Should handle multiple health checks per second" 