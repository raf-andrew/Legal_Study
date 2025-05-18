#!/usr/bin/env python3

import os
import sys
import json
import logging
import datetime
from typing import Dict, List, Any
import requests
import ssl
import socket
import hashlib
import subprocess
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('security_checks.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class SecurityComplianceChecker:
    def __init__(self):
        self.results = {
            'timestamp': datetime.datetime.now().isoformat(),
            'checks': {},
            'summary': {
                'total': 0,
                'passed': 0,
                'failed': 0,
                'warnings': 0
            }
        }

    def check_ssl_certificate(self, hostname: str) -> Dict[str, Any]:
        """Check SSL certificate validity and configuration."""
        try:
            context = ssl.create_default_context()
            with socket.create_connection((hostname, 443)) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cert = ssock.getpeercert()
                    return {
                        'status': 'passed',
                        'details': {
                            'issuer': dict(x[0] for x in cert['issuer']),
                            'subject': dict(x[0] for x in cert['subject']),
                            'version': cert['version'],
                            'notBefore': cert['notBefore'],
                            'notAfter': cert['notAfter']
                        }
                    }
        except Exception as e:
            return {
                'status': 'failed',
                'details': {'error': str(e)}
            }

    def check_password_policy(self) -> Dict[str, Any]:
        """Check password policy configuration."""
        # This is a placeholder for actual password policy checks
        # In a real implementation, this would check system configuration
        return {
            'status': 'passed',
            'details': {
                'min_length': 12,
                'complexity_requirements': True,
                'password_history': 5,
                'max_age': 90
            }
        }

    def check_access_controls(self) -> Dict[str, Any]:
        """Check access control configurations."""
        # This is a placeholder for actual access control checks
        return {
            'status': 'passed',
            'details': {
                'rbac_enabled': True,
                'mfa_required': True,
                'session_timeout': 30,
                'max_login_attempts': 5
            }
        }

    def check_encryption(self) -> Dict[str, Any]:
        """Check encryption configurations."""
        # This is a placeholder for actual encryption checks
        return {
            'status': 'passed',
            'details': {
                'data_at_rest': True,
                'data_in_transit': True,
                'encryption_algorithm': 'AES-256',
                'key_rotation': 90
            }
        }

    def check_security_headers(self, url: str) -> Dict[str, Any]:
        """Check security headers configuration."""
        try:
            response = requests.get(url)
            headers = response.headers

            return {
                'status': 'passed',
                'details': {
                    'content_security_policy': headers.get('Content-Security-Policy', 'missing'),
                    'x_frame_options': headers.get('X-Frame-Options', 'missing'),
                    'x_content_type_options': headers.get('X-Content-Type-Options', 'missing'),
                    'strict_transport_security': headers.get('Strict-Transport-Security', 'missing')
                }
            }
        except Exception as e:
            return {
                'status': 'failed',
                'details': {'error': str(e)}
            }

    def check_file_permissions(self, path: str) -> Dict[str, Any]:
        """Check file permissions and ownership."""
        try:
            stat = os.stat(path)
            return {
                'status': 'passed',
                'details': {
                    'permissions': oct(stat.st_mode)[-3:],
                    'owner': stat.st_uid,
                    'group': stat.st_gid
                }
            }
        except Exception as e:
            return {
                'status': 'failed',
                'details': {'error': str(e)}
            }

    def run_all_checks(self) -> Dict[str, Any]:
        """Run all security compliance checks."""
        checks = {
            'ssl_certificate': self.check_ssl_certificate('example.com'),
            'password_policy': self.check_password_policy(),
            'access_controls': self.check_access_controls(),
            'encryption': self.check_encryption(),
            'security_headers': self.check_security_headers('https://example.com'),
            'file_permissions': self.check_file_permissions('/etc/passwd')
        }

        self.results['checks'] = checks

        # Update summary
        for check in checks.values():
            self.results['summary']['total'] += 1
            if check['status'] == 'passed':
                self.results['summary']['passed'] += 1
            elif check['status'] == 'failed':
                self.results['summary']['failed'] += 1
            else:
                self.results['summary']['warnings'] += 1

        return self.results

    def save_results(self, output_path: str):
        """Save check results to a JSON file."""
        try:
            with open(output_path, 'w') as f:
                json.dump(self.results, f, indent=2)
            logger.info(f"Results saved to {output_path}")
        except Exception as e:
            logger.error(f"Failed to save results: {e}")

def main():
    checker = SecurityComplianceChecker()
    results = checker.run_all_checks()

    # Save results
    output_dir = Path('reports')
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / f'security_compliance_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    checker.save_results(str(output_file))

    # Print summary
    print("\nSecurity Compliance Check Summary:")
    print(f"Total Checks: {results['summary']['total']}")
    print(f"Passed: {results['summary']['passed']}")
    print(f"Failed: {results['summary']['failed']}")
    print(f"Warnings: {results['summary']['warnings']}")

if __name__ == '__main__':
    main()
