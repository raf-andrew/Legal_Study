#!/usr/bin/env python3
"""
Error Handling Test Script
This script tests error handling and recovery mechanisms.
"""

import os
import sys
import json
import logging
import time
import requests
import psycopg2
import redis
import pika
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('error_handling_tests.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class ErrorHandlingTester:
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "tests": {},
            "overall_status": "pending",
            "execution_time": 0,
            "summary": {}
        }
        
        # Define test configurations
        self.test_configs = {
            "api_errors": {
                "endpoint": "http://localhost:8000/api/test",
                "test_cases": [
                    {
                        "name": "invalid_request",
                        "method": "POST",
                        "data": {"invalid": "data"},
                        "expected_status": 400,
                        "expected_fields": ["error", "message"]
                    },
                    {
                        "name": "missing_auth",
                        "method": "GET",
                        "headers": {},
                        "expected_status": 401,
                        "expected_fields": ["error", "message"]
                    },
                    {
                        "name": "invalid_auth",
                        "method": "GET",
                        "headers": {"Authorization": "Bearer invalid_token"},
                        "expected_status": 401,
                        "expected_fields": ["error", "message"]
                    },
                    {
                        "name": "not_found",
                        "method": "GET",
                        "endpoint_suffix": "/nonexistent",
                        "expected_status": 404,
                        "expected_fields": ["error", "message"]
                    },
                    {
                        "name": "method_not_allowed",
                        "method": "PUT",
                        "data": {},
                        "expected_status": 405,
                        "expected_fields": ["error", "message"]
                    }
                ]
            },
            "database_errors": {
                "connection": {
                    "host": "localhost",
                    "port": 5432,
                    "name": "platform_db",
                    "user": "platform_user",
                    "password": "platform_pass"
                },
                "test_cases": [
                    {
                        "name": "invalid_query",
                        "query": "SELECT * FROM nonexistent_table",
                        "expected_error": "relation.*does not exist"
                    },
                    {
                        "name": "duplicate_key",
                        "setup_query": "INSERT INTO users (username) VALUES ('test_user')",
                        "test_query": "INSERT INTO users (username) VALUES ('test_user')",
                        "expected_error": "duplicate key.*violates unique constraint"
                    },
                    {
                        "name": "constraint_violation",
                        "query": "INSERT INTO users (username) VALUES (NULL)",
                        "expected_error": "null value.*violates not-null constraint"
                    }
                ]
            },
            "cache_errors": {
                "connection": {
                    "host": "localhost",
                    "port": 6379,
                    "db": 0
                },
                "test_cases": [
                    {
                        "name": "invalid_key",
                        "operation": "get",
                        "key": "nonexistent_key",
                        "expected_result": None
                    },
                    {
                        "name": "invalid_type",
                        "operation": "incr",
                        "key": "string_key",
                        "setup": {"operation": "set", "key": "string_key", "value": "not_a_number"},
                        "expected_error": "value is not an integer"
                    }
                ]
            },
            "queue_errors": {
                "connection": {
                    "host": "localhost",
                    "port": 5672,
                    "queue": "test_queue"
                },
                "test_cases": [
                    {
                        "name": "nonexistent_queue",
                        "operation": "publish",
                        "queue": "nonexistent_queue",
                        "message": "test_message",
                        "expected_error": "NO_ROUTE"
                    },
                    {
                        "name": "connection_error",
                        "operation": "connect",
                        "host": "nonexistent_host",
                        "expected_error": "connection.*refused"
                    }
                ]
            },
            "recovery_scenarios": {
                "test_cases": [
                    {
                        "name": "database_reconnect",
                        "steps": [
                            {"action": "disconnect_db", "wait": 5},
                            {"action": "reconnect_db", "max_attempts": 3}
                        ]
                    },
                    {
                        "name": "cache_reconnect",
                        "steps": [
                            {"action": "disconnect_cache", "wait": 5},
                            {"action": "reconnect_cache", "max_attempts": 3}
                        ]
                    },
                    {
                        "name": "queue_reconnect",
                        "steps": [
                            {"action": "disconnect_queue", "wait": 5},
                            {"action": "reconnect_queue", "max_attempts": 3}
                        ]
                    }
                ]
            }
        }

    def test_api_errors(self) -> Dict:
        """Test API error handling"""
        config = self.test_configs["api_errors"]
        results = []
        
        for test_case in config["test_cases"]:
            try:
                endpoint = config["endpoint"]
                if "endpoint_suffix" in test_case:
                    endpoint += test_case["endpoint_suffix"]
                
                # Make request
                if test_case["method"] == "GET":
                    response = requests.get(
                        endpoint,
                        headers=test_case.get("headers", {})
                    )
                elif test_case["method"] == "POST":
                    response = requests.post(
                        endpoint,
                        json=test_case.get("data", {}),
                        headers=test_case.get("headers", {})
                    )
                elif test_case["method"] == "PUT":
                    response = requests.put(
                        endpoint,
                        json=test_case.get("data", {}),
                        headers=test_case.get("headers", {})
                    )
                
                # Verify response
                response_data = response.json()
                has_fields = all(
                    field in response_data
                    for field in test_case["expected_fields"]
                )
                
                results.append({
                    "test_case": test_case["name"],
                    "status": "pass" if (
                        response.status_code == test_case["expected_status"] and
                        has_fields
                    ) else "fail",
                    "actual_status": response.status_code,
                    "has_fields": has_fields,
                    "response": response_data
                })
            except Exception as e:
                logger.error(f"Error in test case {test_case['name']}: {e}")
                results.append({
                    "test_case": test_case["name"],
                    "status": "error",
                    "error": str(e)
                })
        
        return {
            "status": "pass" if all(r["status"] == "pass" for r in results) else "fail",
            "results": results
        }

    def test_database_errors(self) -> Dict:
        """Test database error handling"""
        config = self.test_configs["database_errors"]
        results = []
        
        try:
            # Connect to database
            conn = psycopg2.connect(
                host=config["connection"]["host"],
                port=config["connection"]["port"],
                dbname=config["connection"]["name"],
                user=config["connection"]["user"],
                password=config["connection"]["password"]
            )
            
            for test_case in config["test_cases"]:
                try:
                    cur = conn.cursor()
                    
                    # Run setup query if provided
                    if "setup_query" in test_case:
                        try:
                            cur.execute(test_case["setup_query"])
                            conn.commit()
                        except Exception:
                            pass  # Ignore setup errors
                    
                    # Run test query
                    query = test_case.get("test_query", test_case["query"])
                    try:
                        cur.execute(query)
                        conn.commit()
                        results.append({
                            "test_case": test_case["name"],
                            "status": "fail",  # Expected an error
                            "message": "Query succeeded when it should have failed"
                        })
                    except Exception as e:
                        import re
                        error_matches = re.search(
                            test_case["expected_error"],
                            str(e),
                            re.IGNORECASE
                        )
                        results.append({
                            "test_case": test_case["name"],
                            "status": "pass" if error_matches else "fail",
                            "error": str(e)
                        })
                    
                    cur.close()
                except Exception as e:
                    logger.error(f"Error in test case {test_case['name']}: {e}")
                    results.append({
                        "test_case": test_case["name"],
                        "status": "error",
                        "error": str(e)
                    })
            
            conn.close()
        except Exception as e:
            logger.error(f"Error connecting to database: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
        
        return {
            "status": "pass" if all(r["status"] == "pass" for r in results) else "fail",
            "results": results
        }

    def test_cache_errors(self) -> Dict:
        """Test cache error handling"""
        config = self.test_configs["cache_errors"]
        results = []
        
        try:
            # Connect to Redis
            redis_client = redis.Redis(
                host=config["connection"]["host"],
                port=config["connection"]["port"],
                db=config["connection"]["db"]
            )
            
            for test_case in config["test_cases"]:
                try:
                    # Run setup if provided
                    if "setup" in test_case:
                        setup = test_case["setup"]
                        if setup["operation"] == "set":
                            redis_client.set(setup["key"], setup["value"])
                    
                    # Run test operation
                    if test_case["operation"] == "get":
                        result = redis_client.get(test_case["key"])
                        results.append({
                            "test_case": test_case["name"],
                            "status": "pass" if result == test_case["expected_result"] else "fail",
                            "result": result
                        })
                    elif test_case["operation"] == "incr":
                        try:
                            redis_client.incr(test_case["key"])
                            results.append({
                                "test_case": test_case["name"],
                                "status": "fail",  # Expected an error
                                "message": "Operation succeeded when it should have failed"
                            })
                        except redis.RedisError as e:
                            import re
                            error_matches = re.search(
                                test_case["expected_error"],
                                str(e),
                                re.IGNORECASE
                            )
                            results.append({
                                "test_case": test_case["name"],
                                "status": "pass" if error_matches else "fail",
                                "error": str(e)
                            })
                except Exception as e:
                    logger.error(f"Error in test case {test_case['name']}: {e}")
                    results.append({
                        "test_case": test_case["name"],
                        "status": "error",
                        "error": str(e)
                    })
        except Exception as e:
            logger.error(f"Error connecting to Redis: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
        
        return {
            "status": "pass" if all(r["status"] == "pass" for r in results) else "fail",
            "results": results
        }

    def test_queue_errors(self) -> Dict:
        """Test message queue error handling"""
        config = self.test_configs["queue_errors"]
        results = []
        
        for test_case in config["test_cases"]:
            try:
                if test_case["operation"] == "connect":
                    try:
                        connection = pika.BlockingConnection(
                            pika.ConnectionParameters(
                                host=test_case["host"],
                                port=config["connection"]["port"]
                            )
                        )
                        results.append({
                            "test_case": test_case["name"],
                            "status": "fail",  # Expected an error
                            "message": "Connection succeeded when it should have failed"
                        })
                        connection.close()
                    except Exception as e:
                        import re
                        error_matches = re.search(
                            test_case["expected_error"],
                            str(e),
                            re.IGNORECASE
                        )
                        results.append({
                            "test_case": test_case["name"],
                            "status": "pass" if error_matches else "fail",
                            "error": str(e)
                        })
                elif test_case["operation"] == "publish":
                    try:
                        connection = pika.BlockingConnection(
                            pika.ConnectionParameters(
                                host=config["connection"]["host"],
                                port=config["connection"]["port"]
                            )
                        )
                        channel = connection.channel()
                        
                        # Try to publish to nonexistent queue
                        channel.basic_publish(
                            exchange='',
                            routing_key=test_case["queue"],
                            body=test_case["message"]
                        )
                        results.append({
                            "test_case": test_case["name"],
                            "status": "fail",  # Expected an error
                            "message": "Publish succeeded when it should have failed"
                        })
                        
                        connection.close()
                    except Exception as e:
                        import re
                        error_matches = re.search(
                            test_case["expected_error"],
                            str(e),
                            re.IGNORECASE
                        )
                        results.append({
                            "test_case": test_case["name"],
                            "status": "pass" if error_matches else "fail",
                            "error": str(e)
                        })
            except Exception as e:
                logger.error(f"Error in test case {test_case['name']}: {e}")
                results.append({
                    "test_case": test_case["name"],
                    "status": "error",
                    "error": str(e)
                })
        
        return {
            "status": "pass" if all(r["status"] == "pass" for r in results) else "fail",
            "results": results
        }

    def test_recovery_scenarios(self) -> Dict:
        """Test system recovery scenarios"""
        config = self.test_configs["recovery_scenarios"]
        results = []
        
        for test_case in config["test_cases"]:
            try:
                success = True
                for step in test_case["steps"]:
                    if step["action"] == "disconnect_db":
                        # Simulate database disconnect
                        time.sleep(step["wait"])
                    elif step["action"] == "reconnect_db":
                        # Try to reconnect to database
                        attempts = 0
                        while attempts < step["max_attempts"]:
                            try:
                                conn = psycopg2.connect(
                                    host=self.test_configs["database_errors"]["connection"]["host"],
                                    port=self.test_configs["database_errors"]["connection"]["port"],
                                    dbname=self.test_configs["database_errors"]["connection"]["name"],
                                    user=self.test_configs["database_errors"]["connection"]["user"],
                                    password=self.test_configs["database_errors"]["connection"]["password"]
                                )
                                conn.close()
                                break
                            except Exception:
                                attempts += 1
                                time.sleep(1)
                        success = attempts < step["max_attempts"]
                    elif step["action"] == "disconnect_cache":
                        # Simulate cache disconnect
                        time.sleep(step["wait"])
                    elif step["action"] == "reconnect_cache":
                        # Try to reconnect to cache
                        attempts = 0
                        while attempts < step["max_attempts"]:
                            try:
                                redis_client = redis.Redis(
                                    host=self.test_configs["cache_errors"]["connection"]["host"],
                                    port=self.test_configs["cache_errors"]["connection"]["port"],
                                    db=self.test_configs["cache_errors"]["connection"]["db"]
                                )
                                redis_client.ping()
                                break
                            except Exception:
                                attempts += 1
                                time.sleep(1)
                        success = attempts < step["max_attempts"]
                    elif step["action"] == "disconnect_queue":
                        # Simulate queue disconnect
                        time.sleep(step["wait"])
                    elif step["action"] == "reconnect_queue":
                        # Try to reconnect to queue
                        attempts = 0
                        while attempts < step["max_attempts"]:
                            try:
                                connection = pika.BlockingConnection(
                                    pika.ConnectionParameters(
                                        host=self.test_configs["queue_errors"]["connection"]["host"],
                                        port=self.test_configs["queue_errors"]["connection"]["port"]
                                    )
                                )
                                connection.close()
                                break
                            except Exception:
                                attempts += 1
                                time.sleep(1)
                        success = attempts < step["max_attempts"]
                
                results.append({
                    "test_case": test_case["name"],
                    "status": "pass" if success else "fail"
                })
            except Exception as e:
                logger.error(f"Error in test case {test_case['name']}: {e}")
                results.append({
                    "test_case": test_case["name"],
                    "status": "error",
                    "error": str(e)
                })
        
        return {
            "status": "pass" if all(r["status"] == "pass" for r in results) else "fail",
            "results": results
        }

    def run_all_tests(self):
        """Run all error handling tests"""
        start_time = time.time()
        
        # Run tests
        self.results["tests"]["api_errors"] = self.test_api_errors()
        self.results["tests"]["database_errors"] = self.test_database_errors()
        self.results["tests"]["cache_errors"] = self.test_cache_errors()
        self.results["tests"]["queue_errors"] = self.test_queue_errors()
        self.results["tests"]["recovery_scenarios"] = self.test_recovery_scenarios()
        
        self.results["execution_time"] = time.time() - start_time
        
        # Calculate overall status
        failed_tests = [test for test in self.results["tests"].values() 
                       if test["status"] != "pass"]
        self.results["overall_status"] = "fail" if failed_tests else "pass"
        
        # Generate summary
        self.generate_summary()
        
        return self.results

    def generate_summary(self):
        """Generate test execution summary"""
        total_tests = len(self.results["tests"])
        passed_tests = sum(1 for test in self.results["tests"].values() 
                          if test["status"] == "pass")
        failed_tests = total_tests - passed_tests
        
        self.results["summary"] = {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "success_rate": (passed_tests / total_tests) * 100 if total_tests > 0 else 0,
            "execution_time": self.results["execution_time"]
        }

    def save_results(self):
        """Save test results to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"test_results/error_handling_tests_{timestamp}.json"
        
        os.makedirs("test_results", exist_ok=True)
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        logger.info(f"Results saved to {results_file}")

    def generate_report(self) -> str:
        """Generate a human-readable test report"""
        report = f"""
Error Handling Test Report
========================
Generated at: {self.results['timestamp']}
Overall Status: {self.results['overall_status'].upper()}
Total Execution Time: {self.results['execution_time']:.2f} seconds

Summary:
--------
Total Tests: {self.results['summary']['total_tests']}
Passed Tests: {self.results['summary']['passed_tests']}
Failed Tests: {self.results['summary']['failed_tests']}
Success Rate: {self.results['summary']['success_rate']:.2f}%

Detailed Results:
---------------
"""
        
        for test_name, test in self.results["tests"].items():
            report += f"\n{test_name.upper()}:"
            report += f"\n  Status: {test['status'].upper()}"
            
            if test.get("error"):
                report += f"\n  Error: {test['error']}"
            elif test.get("results"):
                report += "\n  Test Cases:"
                for result in test["results"]:
                    report += f"\n    - {result['test_case']}: {result['status'].upper()}"
                    if result.get("error"):
                        report += f"\n      Error: {result['error']}"
            
            report += "\n"
        
        return report

def main():
    tester = ErrorHandlingTester()
    results = tester.run_all_tests()
    tester.save_results()
    
    # Print report
    print(tester.generate_report())
    
    # Exit with appropriate status code
    sys.exit(0 if results["overall_status"] == "pass" else 1)

if __name__ == "__main__":
    main() 