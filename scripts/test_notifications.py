#!/usr/bin/env python3
"""
Notification System Testing Script
This script tests the notification system functionality
"""

import os
import sys
import logging
import json
import time
import requests
from pathlib import Path
from typing import Dict, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('notification_testing.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class NotificationTester:
    def __init__(self):
        self.results = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "tests": {},
            "overall_status": "pending"
        }
        self.notification_endpoint = "http://localhost:8002/notifications"
        self.test_data = self._load_test_data()

    def _load_test_data(self) -> Dict:
        """Load test data from file"""
        test_data_path = Path("tests/data/notification_test_data.json")
        if test_data_path.exists():
            with open(test_data_path) as f:
                return json.load(f)
        return {
            "email": {
                "to": "test@example.com",
                "subject": "Test Email",
                "body": "This is a test email"
            },
            "push": {
                "user_id": "test_user",
                "title": "Test Notification",
                "message": "This is a test notification"
            },
            "templates": {
                "welcome": {
                    "name": "John Doe",
                    "company": "Test Corp"
                },
                "alert": {
                    "type": "warning",
                    "message": "System alert"
                }
            }
        }

    def test_email_sending(self) -> Dict:
        """Test email notification functionality"""
        results = {}

        # Test basic email
        try:
            response = requests.post(
                f"{self.notification_endpoint}/email",
                json=self.test_data["email"]
            )
            results["basic_email"] = {
                "status": response.status_code,
                "response_time": response.elapsed.total_seconds(),
                "message_id": response.json().get("message_id")
            }
        except requests.exceptions.RequestException as e:
            results["basic_email"] = {"error": str(e)}

        # Test HTML email
        try:
            html_data = self.test_data["email"].copy()
            html_data["html"] = "<h1>Test HTML Email</h1>"
            response = requests.post(
                f"{self.notification_endpoint}/email",
                json=html_data
            )
            results["html_email"] = {
                "status": response.status_code,
                "response_time": response.elapsed.total_seconds(),
                "message_id": response.json().get("message_id")
            }
        except requests.exceptions.RequestException as e:
            results["html_email"] = {"error": str(e)}

        return results

    def test_push_notifications(self) -> Dict:
        """Test push notification functionality"""
        results = {}

        # Test basic push notification
        try:
            response = requests.post(
                f"{self.notification_endpoint}/push",
                json=self.test_data["push"]
            )
            results["basic_push"] = {
                "status": response.status_code,
                "response_time": response.elapsed.total_seconds(),
                "notification_id": response.json().get("notification_id")
            }
        except requests.exceptions.RequestException as e:
            results["basic_push"] = {"error": str(e)}

        # Test scheduled push notification
        try:
            scheduled_data = self.test_data["push"].copy()
            scheduled_data["schedule_time"] = (time.time() + 3600) * 1000  # 1 hour from now
            response = requests.post(
                f"{self.notification_endpoint}/push/schedule",
                json=scheduled_data
            )
            results["scheduled_push"] = {
                "status": response.status_code,
                "response_time": response.elapsed.total_seconds(),
                "schedule_id": response.json().get("schedule_id")
            }
        except requests.exceptions.RequestException as e:
            results["scheduled_push"] = {"error": str(e)}

        return results

    def test_templates(self) -> Dict:
        """Test notification templates"""
        results = {}

        for template_name, template_data in self.test_data["templates"].items():
            try:
                response = requests.post(
                    f"{self.notification_endpoint}/template/{template_name}",
                    json=template_data
                )
                results[template_name] = {
                    "status": response.status_code,
                    "response_time": response.elapsed.total_seconds(),
                    "rendered_content": response.json().get("content")
                }
            except requests.exceptions.RequestException as e:
                results[template_name] = {"error": str(e)}

        return results

    def test_rate_limiting(self) -> Dict:
        """Test rate limiting functionality"""
        results = {
            "attempts": [],
            "rate_limited": False
        }

        # Send multiple requests in quick succession
        for i in range(10):
            try:
                response = requests.post(
                    f"{self.notification_endpoint}/email",
                    json=self.test_data["email"]
                )
                results["attempts"].append({
                    "attempt": i + 1,
                    "status": response.status_code,
                    "response_time": response.elapsed.total_seconds()
                })
                if response.status_code == 429:  # Rate limit reached
                    results["rate_limited"] = True
                    break
                time.sleep(0.1)  # Small delay between requests
            except requests.exceptions.RequestException as e:
                results["attempts"].append({
                    "attempt": i + 1,
                    "error": str(e)
                })

        return results

    def test_error_handling(self) -> Dict:
        """Test error handling"""
        test_cases = [
            {"case": "invalid_email", "data": {"to": "invalid-email", "subject": "Test", "body": "Test"}},
            {"case": "missing_recipient", "data": {"subject": "Test", "body": "Test"}},
            {"case": "empty_message", "data": {"to": "test@example.com", "subject": "Test", "body": ""}},
            {"case": "invalid_template", "data": {"template": "nonexistent", "data": {}}}
        ]

        results = {}
        for test in test_cases:
            try:
                response = requests.post(
                    f"{self.notification_endpoint}/email",
                    json=test["data"]
                )
                results[test["case"]] = {
                    "status": response.status_code,
                    "response_time": response.elapsed.total_seconds(),
                    "error_handled": response.status_code != 200
                }
            except requests.exceptions.RequestException as e:
                results[test["case"]] = {"error": str(e)}

        return results

    def run_tests(self):
        """Run all notification tests"""
        logger.info("Starting notification system tests")

        # Test email functionality
        self.results["tests"]["email"] = self.test_email_sending()

        # Test push notifications
        self.results["tests"]["push"] = self.test_push_notifications()

        # Test templates
        self.results["tests"]["templates"] = self.test_templates()

        # Test rate limiting
        self.results["tests"]["rate_limiting"] = self.test_rate_limiting()

        # Test error handling
        self.results["tests"]["error_handling"] = self.test_error_handling()

        # Update overall status
        self._update_overall_status()

        # Save results
        self._save_results()

        logger.info("Notification system tests completed")
        return self.results

    def _update_overall_status(self):
        """Update the overall status based on test results"""
        statuses = []
        for test_suite in self.results["tests"].values():
            if isinstance(test_suite, dict):
                for test in test_suite.values():
                    if isinstance(test, dict):
                        status = test.get("status")
                        if isinstance(status, int):
                            statuses.append(200 <= status < 300)

        if not statuses:
            self.results["overall_status"] = "unknown"
        elif all(statuses):
            self.results["overall_status"] = "success"
        elif any(statuses):
            self.results["overall_status"] = "partial"
        else:
            self.results["overall_status"] = "failure"

    def _save_results(self):
        """Save test results to file"""
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        output_file = f"notification_test_results_{timestamp}.json"

        with open(output_file, 'w') as f:
            json.dump(self.results, f, indent=2)

        logger.info(f"Results saved to {output_file}")

def main():
    """Main function"""
    try:
        tester = NotificationTester()
        results = tester.run_tests()

        # Print summary
        print("\nNotification System Test Summary:")
        print(f"Overall Status: {results['overall_status']}")
        print("\nTest Results:")
        for test_suite, suite_results in results["tests"].items():
            print(f"\n{test_suite.upper()}:")
            for test, result in suite_results.items():
                if isinstance(result, dict):
                    status = result.get("status", "unknown")
                    print(f"  {test}: {status}")

    except Exception as e:
        logger.error(f"Notification system tests failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
