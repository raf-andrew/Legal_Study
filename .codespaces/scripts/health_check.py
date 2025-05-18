import os
import sys
import json
import logging
import mysql.connector
import redis
from datetime import datetime
from pathlib import Path

# Configure logging
log_dir = Path('.codespaces/logs')
log_dir.mkdir(parents=True, exist_ok=True)
log_file = log_dir / f'health_check_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)

class CodespacesHealthCheck:
    def __init__(self):
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'services': {}
        }
        self.verification_dir = Path('.codespaces/verification')
        self.verification_dir.mkdir(parents=True, exist_ok=True)

    def check_mysql(self):
        try:
            conn = mysql.connector.connect(
                host='codespaces-mysql',
                port=3306,
                user='root',
                password='root',
                database='legal_study'
            )
            conn.close()
            return True
        except Exception as e:
            logging.error(f"MySQL health check failed: {str(e)}")
            return False

    def check_redis(self):
        try:
            r = redis.Redis(
                host='codespaces-redis',
                port=6379,
                db=0,
                socket_timeout=5
            )
            r.ping()
            return True
        except Exception as e:
            logging.error(f"Redis health check failed: {str(e)}")
            return False

    def run_health_check(self):
        logging.info("Starting Codespaces health check...")

        # Check MySQL
        mysql_healthy = self.check_mysql()
        self.results['services']['mysql'] = {
            'status': 'healthy' if mysql_healthy else 'unhealthy',
            'timestamp': datetime.now().isoformat()
        }

        # Check Redis
        redis_healthy = self.check_redis()
        self.results['services']['redis'] = {
            'status': 'healthy' if redis_healthy else 'unhealthy',
            'timestamp': datetime.now().isoformat()
        }

        # Save results
        self.save_results()

        # Determine overall health
        all_healthy = mysql_healthy and redis_healthy
        status = "healthy" if all_healthy else "unhealthy"
        logging.info(f"Health check completed. Overall status: {status}")

        return all_healthy

    def save_results(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_file = self.verification_dir / f'health_check_{timestamp}.json'

        with open(result_file, 'w') as f:
            json.dump(self.results, f, indent=2)

        # If all services are healthy, move to complete directory
        if all(service['status'] == 'healthy' for service in self.results['services'].values()):
            complete_dir = Path('.codespaces/complete')
            complete_dir.mkdir(parents=True, exist_ok=True)
            os.rename(result_file, complete_dir / f'health_check_{timestamp}.json')

def main():
    health_check = CodespacesHealthCheck()
    success = health_check.run_health_check()
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
