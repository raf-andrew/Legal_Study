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
log_file = log_dir / f'feature_tests_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)

class FeatureTestRunner:
    def __init__(self):
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'tests': []
        }
        self.verification_dir = Path('.codespaces/verification')
        self.verification_dir.mkdir(parents=True, exist_ok=True)

    def run_tests(self):
        logging.info("Starting feature tests...")

        try:
            # Run Laravel feature tests
            result = subprocess.run(
                ['php', 'artisan', 'test', '--testsuite=Feature'],
                capture_output=True,
                text=True
            )

            # Parse test results
            success = result.returncode == 0
            output = result.stdout + result.stderr

            # Save test results
            self.results['tests'].append({
                'status': 'passed' if success else 'failed',
                'output': output,
                'timestamp': datetime.now().isoformat()
            })

            # Save results
            self.save_results(success)

            if success:
                logging.info("Feature tests completed successfully")
            else:
                logging.error("Feature tests failed")

            return success

        except Exception as e:
            logging.error(f"Error running feature tests: {str(e)}")
            return False

    def save_results(self, success):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_file = self.verification_dir / f'feature_tests_{timestamp}.json'

        with open(result_file, 'w') as f:
            json.dump(self.results, f, indent=2)

        # If tests passed, move to complete directory
        if success:
            complete_dir = Path('.codespaces/complete')
            complete_dir.mkdir(parents=True, exist_ok=True)
            os.rename(result_file, complete_dir / f'feature_tests_{timestamp}.json')

            # Update checklist
            self.update_checklist(timestamp)

    def update_checklist(self, timestamp):
        checklist_file = Path('.codespaces/checklist/feature_tests.md')
        checklist_file.parent.mkdir(parents=True, exist_ok=True)

        if not checklist_file.exists():
            with open(checklist_file, 'w') as f:
                f.write("# Feature Tests Checklist\n\n")
                f.write("## Completed Tests\n\n")

        with open(checklist_file, 'a') as f:
            f.write(f"- [x] Feature Tests {timestamp} - [Report](.codespaces/complete/feature_tests_{timestamp}.json)\n")

def main():
    test_runner = FeatureTestRunner()
    success = test_runner.run_tests()
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
