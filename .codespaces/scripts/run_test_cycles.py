import os
import sys
import json
import logging
import subprocess
from datetime import datetime
from pathlib import Path

# Configure logging
log_dir = Path('.codespaces/logs')
log_dir.mkdir(parents=True, exist_ok=True)
log_file = log_dir / f'test_cycles_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)

class TestCycleRunner:
    def __init__(self):
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'cycles': []
        }
        self.verification_dir = Path('.codespaces/verification')
        self.verification_dir.mkdir(parents=True, exist_ok=True)

    def run_health_check(self):
        logging.info("Running health check...")
        try:
            result = subprocess.run(
                ['python', '.codespaces/scripts/health_check.py'],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except Exception as e:
            logging.error(f"Health check failed: {str(e)}")
            return False

    def run_feature_tests(self):
        logging.info("Running feature tests...")
        try:
            result = subprocess.run(
                ['python', '.codespaces/scripts/run_feature_tests.py'],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except Exception as e:
            logging.error(f"Feature tests failed: {str(e)}")
            return False

    def run_cycle(self, cycle_number):
        logging.info(f"Starting test cycle {cycle_number}...")

        # Run health check
        if not self.run_health_check():
            logging.error("Health check failed, skipping cycle")
            return False

        # Run feature tests
        if not self.run_feature_tests():
            logging.error("Feature tests failed")
            return False

        logging.info(f"Test cycle {cycle_number} completed successfully")
        return True

    def run_cycles(self, num_cycles=10):
        logging.info(f"Starting {num_cycles} test cycles...")

        for i in range(1, num_cycles + 1):
            cycle_result = self.run_cycle(i)
            self.results['cycles'].append({
                'cycle_number': i,
                'status': 'passed' if cycle_result else 'failed',
                'timestamp': datetime.now().isoformat()
            })

            if not cycle_result:
                logging.error(f"Test cycle {i} failed")
                break

        # Save results
        self.save_results()

    def save_results(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_file = self.verification_dir / f'test_cycles_{timestamp}.json'

        with open(result_file, 'w') as f:
            json.dump(self.results, f, indent=2)

        # If all cycles passed, move to complete directory
        if all(cycle['status'] == 'passed' for cycle in self.results['cycles']):
            complete_dir = Path('.codespaces/complete')
            complete_dir.mkdir(parents=True, exist_ok=True)
            os.rename(result_file, complete_dir / f'test_cycles_{timestamp}.json')

            # Update checklist
            self.update_checklist(timestamp)

    def update_checklist(self, timestamp):
        checklist_file = Path('.codespaces/checklist/feature_tests.md')
        checklist_file.parent.mkdir(parents=True, exist_ok=True)

        if not checklist_file.exists():
            with open(checklist_file, 'w') as f:
                f.write("# Feature Tests Checklist\n\n")
                f.write("## Completed Test Cycles\n\n")

        with open(checklist_file, 'a') as f:
            f.write(f"- [x] Test Cycles {timestamp} - [Report](.codespaces/complete/test_cycles_{timestamp}.json)\n")

def main():
    cycle_runner = TestCycleRunner()
    cycle_runner.run_cycles()
    sys.exit(0)

if __name__ == '__main__':
    main()
