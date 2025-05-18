from locust import HttpUser, task, between
from typing import Dict, Any
import json
import yaml

class ConsoleCommandUser(HttpUser):
    """User class for console command load testing."""
    wait_time = between(1, 2)

    def on_start(self):
        """Initialize user session."""
        # Get authentication token
        response = self.client.post("/auth/token", json={
            "username": "test_user",
            "password": "test_password"
        })
        self.token = response.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}

    @task(3)
    def check_health(self):
        """Test health check endpoint."""
        self.client.get("/health", headers=self.headers)

    @task(2)
    def check_directories(self):
        """Test directory check endpoint."""
        self.client.get("/check/directories", headers=self.headers)

    @task(2)
    def check_configurations(self):
        """Test configuration check endpoint."""
        self.client.get("/check/configurations", headers=self.headers)

    @task(1)
    def generate_report(self):
        """Test report generation endpoint."""
        response = self.client.post(
            "/check/report",
            headers=self.headers,
            json={
                "checks": ["directories", "configurations"],
                "format": "json"
            }
        )
        assert response.status_code == 200
        assert "checks" in response.json()

    @task(1)
    def update_configuration(self):
        """Test configuration update endpoint."""
        config = {
            "general": {
                "environment": "test",
                "debug": True
            }
        }
        response = self.client.put(
            "/config/console.yaml",
            headers=self.headers,
            json=config
        )
        assert response.status_code == 200

class ConsoleCommandStressTest(HttpUser):
    """User class for console command stress testing."""
    wait_time = between(0.1, 0.5)

    def on_start(self):
        """Initialize user session."""
        # Get authentication token
        response = self.client.post("/auth/token", json={
            "username": f"stress_user_{self.user_id}",
            "password": "stress_password"
        })
        self.token = response.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}

    @task
    def rapid_health_checks(self):
        """Rapid health check requests."""
        self.client.get("/health", headers=self.headers)

    @task
    def concurrent_report_generation(self):
        """Concurrent report generation requests."""
        checks = ["directories", "configurations", "security", "monitoring"]
        for check in checks:
            self.client.post(
                "/check/report",
                headers=self.headers,
                json={
                    "checks": [check],
                    "format": "json"
                }
            )

    @task
    def bulk_configuration_updates(self):
        """Bulk configuration update requests."""
        configs = []
        for i in range(10):
            configs.append({
                "name": f"config_{i}",
                "value": f"value_{i}"
            })
        
        self.client.put(
            "/config/bulk",
            headers=self.headers,
            json={"configs": configs}
        )

def run_load_test():
    """Run load test with specific parameters."""
    import subprocess
    subprocess.run([
        "locust",
        "-f", __file__,
        "--host=http://localhost:8000",
        "--users", "100",
        "--spawn-rate", "10",
        "--run-time", "5m",
        "--headless",
        "--only-summary"
    ])

def run_stress_test():
    """Run stress test with specific parameters."""
    import subprocess
    subprocess.run([
        "locust",
        "-f", __file__,
        "--host=http://localhost:8000",
        "--users", "1000",
        "--spawn-rate", "100",
        "--run-time", "10m",
        "--headless",
        "--only-summary"
    ])

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "stress":
        run_stress_test()
    else:
        run_load_test() 