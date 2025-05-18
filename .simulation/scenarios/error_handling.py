import logging
import time
import random
from pathlib import Path

logger = logging.getLogger(__name__)

class ErrorHandlingSimulation:
    def __init__(self, base_dir=".simulation"):
        self.base_dir = Path(base_dir)
        self.results_dir = self.base_dir / "results"
        self.error_types = {
            "data_processing": [
                "Invalid data format detected",
                "Missing required fields",
                "Data validation failed",
                "Processing timeout exceeded"
            ],
            "validation": [
                "Schema validation failed",
                "Data integrity check failed",
                "Business rule violation",
                "Reference data mismatch"
            ],
            "completion": [
                "Resource allocation failed",
                "State transition error",
                "Cleanup operation failed",
                "Finalization timeout"
            ]
        }

    def run(self, iteration):
        logger.info(f"Starting error handling simulation - iteration {iteration}")
        steps = {}
        overall_status = "success"
        error_recovery_triggered = False
        error_message = None

        # Simulate initialization
        steps["initialization"] = {
            "status": "success",
            "message": "Initialization succeeded",
            "duration": 0.1
        }

        # Simulate potential failure in data processing
        if random.random() < 0.4:  # 40% chance of failure
            error_type = "data_processing"
            error_message = random.choice(self.error_types[error_type])
            steps[error_type] = {
                "status": "failure",
                "message": error_message,
                "duration": 0.2,
                "error_details": {
                    "error_code": f"ERR_{error_type.upper()}_{random.randint(100, 999)}",
                    "severity": random.choice(["low", "medium", "high"]),
                    "affected_components": random.randint(1, 3)
                }
            }
            overall_status = "failure"
            error_recovery_triggered = True

            # Simulate error recovery
            steps["error_recovery"] = {
                "status": "recovered",
                "message": "Error recovery procedure executed",
                "duration": 0.05,
                "recovery_details": {
                    "recovery_steps": random.randint(2, 5),
                    "recovery_time": round(random.uniform(0.1, 0.5), 2),
                    "recovery_success_rate": round(random.uniform(0.8, 1.0), 2)
                }
            }
        else:
            # Simulate successful data processing
            steps["data_processing"] = {
                "status": "success",
                "message": "Data processing completed",
                "duration": 0.2
            }

            # Simulate validation
            steps["validation"] = {
                "status": "success",
                "message": "Validation succeeded",
                "duration": 0.15
            }

            # Simulate completion
            steps["completion"] = {
                "status": "success",
                "message": "Completion completed",
                "duration": 0.1
            }

        return {
            "iteration": iteration,
            "status": overall_status,
            "steps": steps,
            "error_recovery_triggered": error_recovery_triggered,
            "error_message": error_message,
            "timestamp": time.time()
        }

    def _simulate_step(self, fail_message, fail_prob=0.1, duration=0.1):
        time.sleep(duration)
        if random.random() < fail_prob:
            return {
                "status": "failure",
                "message": fail_message,
                "duration": duration
            }
        else:
            return {
                "status": "success",
                "message": fail_message.replace("failed", "succeeded").replace("error", "completed"),
                "duration": duration
            }

    def _simulate_recovery(self):
        time.sleep(0.05)
        return {
            "status": "recovered",
            "message": "Error recovery procedure executed",
            "duration": 0.05
        }

    def _format_result(self, iteration, overall_status, steps, error_recovery_triggered, error_message):
        return {
            "iteration": iteration,
            "status": overall_status,
            "steps": steps,
            "error_recovery_triggered": error_recovery_triggered,
            "error_message": error_message,
            "timestamp": time.time()
        }
