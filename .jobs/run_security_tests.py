import subprocess
import json
import logging
import os
import sys
import requests
import ssl
import socket
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urljoin

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SecurityTester:
    def __init__(self, config_path: str = "config/security_tests.json"):
        self.config = self._load_config(config_path)
        self.results = {}
        
    def _load_config(self, config_path: str) -> Dict:
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"Config file not found at {config_path}, using defaults")
            return {
                "base_url": "http://localhost:8000",
                "endpoints": {
                    "auth": "/auth",
                    "api": "/api",
                    "ai": "/ai",
                    "notifications": "/notifications"
                },
                "auth": {
                    "test_user": "test@example.com",
                    "test_password": "TestPassword123!"
                },
                "security_headers": [
                    "X-Content-Type-Options",
                    "X-Frame-Options",
                    "X-XSS-Protection",
                    "Content-Security-Policy",
                    "Strict-Transport-Security"
                ],
                "rate_limits": {
                    "auth": 5,
                    "api": 100,
                    "notifications": 50
                }
            }

    def test_ssl_configuration(self, hostname: str, port: int = 443) -> Dict:
        """Test SSL/TLS configuration."""
        try:
            context = ssl.create_default_context()
            with socket.create_connection((hostname, port)) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cert = ssock.getpeercert()
                    cipher = ssock.cipher()
                    version = ssock.version()
                    
                    return {
                        "status": "secure",
                        "protocol_version": version,
                        "cipher_suite": cipher[0],
                        "certificate": {
                            "subject": dict(x[0] for x in cert["subject"]),
                            "issuer": dict(x[0] for x in cert["issuer"]),
                            "valid_from": cert["notBefore"],
                            "valid_until": cert["notAfter"]
                        }
                    }
        except Exception as e:
            return {
                "status": "insecure",
                "error": str(e)
            }

    def test_security_headers(self, url: str) -> Dict:
        """Test security headers."""
        try:
            response = requests.head(url, allow_redirects=True)
            headers = response.headers
            
            results = {}
            for header in self.config["security_headers"]:
                results[header] = {
                    "present": header in headers,
                    "value": headers.get(header, None)
                }
            
            return {
                "status": "secure" if all(r["present"] for r in results.values()) else "warning",
                "headers": results
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

    def test_authentication(self, auth_url: str) -> Dict:
        """Test authentication security."""
        results = {
            "login": self._test_login(auth_url),
            "brute_force": self._test_brute_force_protection(auth_url),
            "password_policy": self._test_password_policy(auth_url),
            "session": self._test_session_security(auth_url)
        }
        
        return {
            "status": "secure" if all(r["status"] == "secure" for r in results.values()) else "warning",
            "tests": results
        }

    def _test_login(self, url: str) -> Dict:
        """Test basic login functionality."""
        try:
            # Test valid login
            response = requests.post(url + "/login", json={
                "email": self.config["auth"]["test_user"],
                "password": self.config["auth"]["test_password"]
            })
            
            valid_login = response.status_code == 200
            
            # Test invalid login
            response = requests.post(url + "/login", json={
                "email": "invalid@example.com",
                "password": "invalid"
            })
            
            invalid_login = response.status_code == 401
            
            return {
                "status": "secure" if valid_login and invalid_login else "warning",
                "valid_login": valid_login,
                "invalid_login": invalid_login
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

    def _test_brute_force_protection(self, url: str) -> Dict:
        """Test brute force protection."""
        try:
            failures = 0
            for _ in range(10):
                response = requests.post(url + "/login", json={
                    "email": "test@example.com",
                    "password": "wrong"
                })
                if response.status_code == 429:  # Too Many Requests
                    break
                failures += 1
            
            return {
                "status": "secure" if failures < 10 else "warning",
                "attempts_before_lockout": failures
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

    def _test_password_policy(self, url: str) -> Dict:
        """Test password policy enforcement."""
        weak_passwords = [
            "password",
            "12345678",
            "qwerty",
            "test123"
        ]
        
        results = []
        try:
            for password in weak_passwords:
                response = requests.post(url + "/register", json={
                    "email": "test@example.com",
                    "password": password
                })
                results.append(response.status_code != 200)
            
            return {
                "status": "secure" if all(results) else "warning",
                "weak_passwords_rejected": all(results)
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

    def _test_session_security(self, url: str) -> Dict:
        """Test session security."""
        try:
            # Login to get session
            response = requests.post(url + "/login", json={
                "email": self.config["auth"]["test_user"],
                "password": self.config["auth"]["test_password"]
            })
            
            if response.status_code != 200:
                return {
                    "status": "error",
                    "error": "Could not login"
                }
            
            cookies = response.cookies
            session_cookie = cookies.get("session")
            
            results = {
                "httponly": session_cookie.has_nonstandard_attr("HttpOnly"),
                "secure": session_cookie.has_nonstandard_attr("secure"),
                "samesite": session_cookie.has_nonstandard_attr("SameSite")
            }
            
            return {
                "status": "secure" if all(results.values()) else "warning",
                "cookie_attributes": results
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

    def test_rate_limiting(self, endpoint: str) -> Dict:
        """Test rate limiting."""
        try:
            results = []
            start_time = datetime.now()
            
            for _ in range(self.config["rate_limits"][endpoint] + 5):
                response = requests.get(urljoin(self.config["base_url"], endpoint))
                results.append(response.status_code)
                
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            rate_limited = 429 in results
            
            return {
                "status": "secure" if rate_limited else "warning",
                "rate_limited": rate_limited,
                "requests_before_limit": results.index(429) if rate_limited else len(results),
                "duration": duration
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

    def run_security_tests(self) -> Dict:
        """Run all security tests."""
        results = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_tests": 0,
                "passed_tests": 0,
                "warning_tests": 0,
                "failed_tests": 0
            },
            "tests": {}
        }
        
        # Test SSL configuration
        hostname = self.config["base_url"].split("://")[1].split(":")[0]
        results["tests"]["ssl"] = self.test_ssl_configuration(hostname)
        
        # Test security headers
        results["tests"]["headers"] = self.test_security_headers(self.config["base_url"])
        
        # Test authentication
        auth_url = urljoin(self.config["base_url"], self.config["endpoints"]["auth"])
        results["tests"]["authentication"] = self.test_authentication(auth_url)
        
        # Test rate limiting
        for endpoint, limit in self.config["rate_limits"].items():
            results["tests"][f"rate_limiting_{endpoint}"] = self.test_rate_limiting(endpoint)
        
        # Update summary
        for test_result in results["tests"].values():
            results["summary"]["total_tests"] += 1
            if test_result["status"] == "secure":
                results["summary"]["passed_tests"] += 1
            elif test_result["status"] == "warning":
                results["summary"]["warning_tests"] += 1
            else:
                results["summary"]["failed_tests"] += 1
        
        self.results = results
        return results

    def generate_report(self, output_format: str = "text") -> str:
        """Generate a security test report."""
        if not self.results:
            self.run_security_tests()
            
        if output_format == "json":
            return json.dumps(self.results, indent=2)
            
        elif output_format == "text":
            report = []
            report.append("Security Test Results")
            report.append(f"Generated: {self.results['timestamp']}")
            
            report.append("\nSummary:")
            report.append(f"Total Tests: {self.results['summary']['total_tests']}")
            report.append(f"Passed: {self.results['summary']['passed_tests']}")
            report.append(f"Warnings: {self.results['summary']['warning_tests']}")
            report.append(f"Failed: {self.results['summary']['failed_tests']}")
            
            for test_name, test_result in self.results["tests"].items():
                report.append(f"\n{test_name.replace('_', ' ').title()}:")
                report.append(f"Status: {test_result['status'].upper()}")
                
                if "error" in test_result:
                    report.append(f"Error: {test_result['error']}")
                else:
                    for key, value in test_result.items():
                        if key != "status":
                            report.append(f"{key}: {value}")
            
            return "\n".join(report)
            
        elif output_format == "html":
            html = [
                "<html>",
                "<head>",
                "<style>",
                "body { font-family: Arial, sans-serif; margin: 20px; }",
                ".secure { color: green; }",
                ".warning { color: orange; }",
                ".error { color: red; }",
                ".test { margin: 20px 0; padding: 10px; border: 1px solid #ccc; }",
                "</style>",
                "</head>",
                "<body>",
                "<h1>Security Test Results</h1>",
                f"<p>Generated: {self.results['timestamp']}</p>"
            ]
            
            # Summary
            html.append("<h2>Summary</h2>")
            html.append("<ul>")
            html.append(f"<li>Total Tests: {self.results['summary']['total_tests']}</li>")
            html.append(f"<li>Passed: <span class='secure'>{self.results['summary']['passed_tests']}</span></li>")
            html.append(f"<li>Warnings: <span class='warning'>{self.results['summary']['warning_tests']}</span></li>")
            html.append(f"<li>Failed: <span class='error'>{self.results['summary']['failed_tests']}</span></li>")
            html.append("</ul>")
            
            # Individual tests
            for test_name, test_result in self.results["tests"].items():
                html.append(f'<div class="test">')
                html.append(f"<h3>{test_name.replace('_', ' ').title()}</h3>")
                html.append(f"<p>Status: <span class='{test_result['status']}'>{test_result['status'].upper()}</span></p>")
                
                if "error" in test_result:
                    html.append(f"<p class='error'>Error: {test_result['error']}</p>")
                else:
                    html.append("<ul>")
                    for key, value in test_result.items():
                        if key != "status":
                            html.append(f"<li><strong>{key}:</strong> {value}</li>")
                    html.append("</ul>")
                
                html.append("</div>")
            
            html.extend(["</body>", "</html>"])
            return "\n".join(html)
        else:
            raise ValueError(f"Unsupported output format: {output_format}")

    def save_report(self, output_dir: str = "reports") -> None:
        """Save security test results in multiple formats."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        os.makedirs(output_dir, exist_ok=True)
        
        # Save JSON report
        with open(f"{output_dir}/security_test_{timestamp}.json", "w") as f:
            json.dump(self.results, f, indent=2)
        
        # Save text report
        with open(f"{output_dir}/security_test_{timestamp}.txt", "w") as f:
            f.write(self.generate_report("text"))
        
        # Save HTML report
        with open(f"{output_dir}/security_test_{timestamp}.html", "w") as f:
            f.write(self.generate_report("html"))

def main():
    tester = SecurityTester()
    
    # Run security tests
    tester.run_security_tests()
    
    # Generate and print text report
    print(tester.generate_report("text"))
    
    # Save reports in all formats
    tester.save_report()
    
    # Exit with appropriate status code
    if tester.results["summary"]["failed_tests"] > 0:
        sys.exit(1)
    sys.exit(0)

if __name__ == "__main__":
    main() 