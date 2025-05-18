import os
import logging
import json
import time
from pathlib import Path
from datetime import datetime
from scenarios.basic_workflow import BasicWorkflowSimulation
from scenarios.error_handling import ErrorHandlingSimulation
from scenarios.performance_test import PerformanceTestSimulation
from scenarios.stress_test import StressTestSimulation
from scenarios.resilience_test import ResilienceTestSimulation

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SimulationRunner:
    def __init__(self, base_dir=".simulation"):
        self.base_dir = Path(base_dir)
        self.results_dir = self.base_dir / "results"
        self.scenarios_dir = self.base_dir / "scenarios"
        self.setup_directories()

        # Initialize scenarios
        self.scenarios = {
            "basic_workflow": BasicWorkflowSimulation(base_dir),
            "error_handling": ErrorHandlingSimulation(base_dir),
            "performance_test": PerformanceTestSimulation(base_dir),
            "stress_test": StressTestSimulation(base_dir),
            "resilience_test": ResilienceTestSimulation(base_dir)
        }

    def setup_directories(self):
        """Create necessary directories if they don't exist"""
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.scenarios_dir.mkdir(parents=True, exist_ok=True)

    def run_simulation(self, scenario_name, iterations=3):
        """Run a simulation for a specific scenario"""
        if scenario_name not in self.scenarios:
            raise ValueError(f"Unknown scenario: {scenario_name}")

        logger.info(f"Starting simulation: {scenario_name}")
        scenario = self.scenarios[scenario_name]

        results = {
            "scenario": scenario_name,
            "start_time": datetime.now().isoformat(),
            "iterations": iterations,
            "results": []
        }

        for i in range(1, iterations + 1):
            logger.info(f"Running iteration {i}/{iterations}")
            iteration_result = scenario.run(i)
            results["results"].append(iteration_result)

        results["end_time"] = datetime.now().isoformat()
        results["duration"] = time.time() - time.mktime(
            datetime.fromisoformat(results["start_time"]).timetuple()
        )

        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.results_dir / f"{scenario_name}_{timestamp}.json"
        with open(output_file, "w") as f:
            json.dump(results, f, indent=2)
        logger.info(f"Results saved to {output_file}")

    def run_all_simulations(self):
        for scenario_name in self.scenarios:
            self.run_simulation(scenario_name)

def main():
    runner = SimulationRunner()
    runner.run_all_simulations()

if __name__ == "__main__":
    main()
