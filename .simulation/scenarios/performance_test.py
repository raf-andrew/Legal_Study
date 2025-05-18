import logging
import time
import random
from pathlib import Path

logger = logging.getLogger(__name__)

class PerformanceTestSimulation:
    def __init__(self, base_dir=".simulation"):
        self.base_dir = Path(base_dir)
        self.results_dir = self.base_dir / "results"

    def run(self, iteration):
        logger.info(f"Starting performance test simulation - iteration {iteration}")
        steps = {}
        overall_status = "success"

        # Simulate different load conditions
        load_level = random.choice(["low", "medium", "high"])
        steps["load_condition"] = {
            "status": "success",
            "message": f"Simulating {load_level} load condition",
            "duration": 0.1
        }

        # Simulate response time based on load
        response_time = self._simulate_response_time(load_level)
        steps["response_time"] = {
            "status": "success",
            "message": f"Response time: {response_time:.3f}s under {load_level} load",
            "duration": response_time
        }

        # Simulate resource utilization
        cpu_usage = random.uniform(20, 90) if load_level == "high" else random.uniform(10, 50)
        memory_usage = random.uniform(30, 95) if load_level == "high" else random.uniform(20, 60)

        steps["resource_utilization"] = {
            "status": "success",
            "message": f"CPU: {cpu_usage:.1f}%, Memory: {memory_usage:.1f}%",
            "duration": 0.1,
            "metrics": {
                "cpu_usage": cpu_usage,
                "memory_usage": memory_usage
            }
        }

        # Simulate throughput
        throughput = self._simulate_throughput(load_level)
        steps["throughput"] = {
            "status": "success",
            "message": f"Throughput: {throughput:.1f} requests/second",
            "duration": 0.1,
            "metrics": {
                "requests_per_second": throughput
            }
        }

        return self._format_result(iteration, overall_status, steps)

    def _simulate_response_time(self, load_level):
        base_time = 0.1
        if load_level == "low":
            return base_time + random.uniform(0, 0.2)
        elif load_level == "medium":
            return base_time + random.uniform(0.2, 0.5)
        else:  # high
            return base_time + random.uniform(0.5, 1.0)

    def _simulate_throughput(self, load_level):
        if load_level == "low":
            return random.uniform(50, 100)
        elif load_level == "medium":
            return random.uniform(20, 50)
        else:  # high
            return random.uniform(5, 20)

    def _format_result(self, iteration, overall_status, steps):
        return {
            "iteration": iteration,
            "status": overall_status,
            "steps": steps,
            "timestamp": time.time()
        }
