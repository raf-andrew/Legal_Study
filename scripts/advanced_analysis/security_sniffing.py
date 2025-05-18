#!/usr/bin/env python3
"""
Security Sniffing Module
This module implements security-specific sniffing functionality
"""

import os
import sys
import logging
import asyncio
import json
import ast
import re
from pathlib import Path
from typing import Dict, List, Optional, Set
from datetime import datetime
from dataclasses import dataclass

from .config import SNIFFING_CONFIG, SECURITY_SIMULATION

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('security_sniffing.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

@dataclass
class SecurityIssue:
    """Data class for security issues"""
    type: str
    severity: str
    description: str
    location: str
    recommendation: str
    cwe_id: Optional[str] = None
    cvss_score: Optional[float] = None

class SecuritySniffer:
    def __init__(self):
        self.config = SNIFFING_CONFIG["domains"]["security"]
        self.thresholds = self.config["thresholds"]
        self.known_vulnerabilities = self._load_known_vulnerabilities()
        self.security_patterns = self._load_security_patterns()

    def _load_known_vulnerabilities(self) -> Dict:
        """Load known vulnerability database"""
        # Load from external source or local database
        return {
            "sql_injection": {
                "patterns": [
                    r"SELECT.*FROM.*WHERE.*=.*'%s'",
                    r"INSERT.*INTO.*VALUES.*'%s'",
                    r"UPDATE.*SET.*=.*'%s'",
                    r"DELETE.*FROM.*WHERE.*=.*'%s'"
                ],
                "cwe_id": "CWE-89",
                "cvss_score": 9.8
            },
            "xss": {
                "patterns": [
                    r"<script>.*</script>",
                    r"javascript:",
                    r"onerror=",
                    r"onload="
                ],
                "cwe_id": "CWE-79",
                "cvss_score": 6.1
            },
            "csrf": {
                "patterns": [
                    r"<form.*action=.*method=.*>",
                    r"<input.*type=.*hidden.*>"
                ],
                "cwe_id": "CWE-352",
                "cvss_score": 8.8
            }
        }

    def _load_security_patterns(self) -> Dict:
        """Load security patterns for analysis"""
        return {
            "hardcoded_credentials": [
                r"password\s*=\s*['\"].*['\"]",
                r"api_key\s*=\s*['\"].*['\"]",
                r"secret\s*=\s*['\"].*['\"]"
            ],
            "insecure_deserialization": [
                r"pickle\.loads\(",
                r"yaml\.load\(",
                r"json\.loads\("
            ],
            "insecure_crypto": [
                r"md5\(",
                r"sha1\(",
                r"DES\.new\("
            ],
            "insecure_headers": [
                r"Access-Control-Allow-Origin: \*",
                r"X-Frame-Options:",
                r"X-Content-Type-Options:"
            ]
        }

    async def sniff_file(self, file_path: str) -> List[SecurityIssue]:
        """Perform security sniffing on a file"""
        logger.info(f"Starting security sniffing for file: {file_path}")

        issues = []

        # Static analysis
        issues.extend(await self._analyze_static(file_path))

        # Dynamic analysis
        issues.extend(await self._analyze_dynamic(file_path))

        # Vulnerability simulation
        issues.extend(await self._simulate_vulnerabilities(file_path))

        return issues

    async def _analyze_static(self, file_path: str) -> List[SecurityIssue]:
        """Perform static security analysis"""
        issues = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Check for hardcoded credentials
            issues.extend(self._check_hardcoded_credentials(content, file_path))

            # Check for insecure deserialization
            issues.extend(self._check_insecure_deserialization(content, file_path))

            # Check for insecure crypto
            issues.extend(self._check_insecure_crypto(content, file_path))

            # Check for SQL injection vulnerabilities
            issues.extend(self._check_sql_injection(content, file_path))

            # Check for XSS vulnerabilities
            issues.extend(self._check_xss(content, file_path))

            # Check for CSRF vulnerabilities
            issues.extend(self._check_csrf(content, file_path))

            # Parse AST for deeper analysis
            tree = ast.parse(content)
            issues.extend(self._analyze_ast(tree, file_path))

        except Exception as e:
            logger.error(f"Error in static analysis for {file_path}: {e}")
            issues.append(SecurityIssue(
                type="analysis_error",
                severity="high",
                description=f"Failed to perform static analysis: {str(e)}",
                location=file_path,
                recommendation="Fix file parsing issues and retry analysis"
            ))

        return issues

    async def _analyze_dynamic(self, file_path: str) -> List[SecurityIssue]:
        """Perform dynamic security analysis"""
        issues = []

        # Implement dynamic analysis
        # - Test API endpoints
        # - Check authentication mechanisms
        # - Test authorization controls
        # - Analyze session management

        return issues

    async def _simulate_vulnerabilities(self, file_path: str) -> List[SecurityIssue]:
        """Simulate security vulnerabilities"""
        issues = []

        for vector in SECURITY_SIMULATION["attack_vectors"]:
            for level in SECURITY_SIMULATION["intensity_levels"]:
                for component in SECURITY_SIMULATION["target_components"]:
                    try:
                        result = await self._simulate_attack(vector, level, component, file_path)
                        if result:
                            issues.append(result)
                    except Exception as e:
                        logger.error(f"Error simulating {vector} attack: {e}")

        return issues

    def _check_hardcoded_credentials(self, content: str, file_path: str) -> List[SecurityIssue]:
        """Check for hardcoded credentials"""
        issues = []

        for pattern in self.security_patterns["hardcoded_credentials"]:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                issues.append(SecurityIssue(
                    type="hardcoded_credential",
                    severity="critical",
                    description=f"Hardcoded credential found: {match.group(0)}",
                    location=f"{file_path}:{content[:match.start()].count('\n') + 1}",
                    recommendation="Move credentials to secure configuration or environment variables",
                    cwe_id="CWE-798",
                    cvss_score=9.8
                ))

        return issues

    def _check_insecure_deserialization(self, content: str, file_path: str) -> List[SecurityIssue]:
        """Check for insecure deserialization"""
        issues = []

        for pattern in self.security_patterns["insecure_deserialization"]:
            matches = re.finditer(pattern, content)
            for match in matches:
                issues.append(SecurityIssue(
                    type="insecure_deserialization",
                    severity="high",
                    description=f"Insecure deserialization found: {match.group(0)}",
                    location=f"{file_path}:{content[:match.start()].count('\n') + 1}",
                    recommendation="Use safe deserialization methods and validate input",
                    cwe_id="CWE-502",
                    cvss_score=8.8
                ))

        return issues

    def _check_insecure_crypto(self, content: str, file_path: str) -> List[SecurityIssue]:
        """Check for insecure cryptographic operations"""
        issues = []

        for pattern in self.security_patterns["insecure_crypto"]:
            matches = re.finditer(pattern, content)
            for match in matches:
                issues.append(SecurityIssue(
                    type="insecure_crypto",
                    severity="high",
                    description=f"Insecure cryptographic operation found: {match.group(0)}",
                    location=f"{file_path}:{content[:match.start()].count('\n') + 1}",
                    recommendation="Use modern cryptographic algorithms and libraries",
                    cwe_id="CWE-326",
                    cvss_score=7.5
                ))

        return issues

    def _check_sql_injection(self, content: str, file_path: str) -> List[SecurityIssue]:
        """Check for SQL injection vulnerabilities"""
        issues = []

        for pattern in self.known_vulnerabilities["sql_injection"]["patterns"]:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                issues.append(SecurityIssue(
                    type="sql_injection",
                    severity="critical",
                    description=f"Potential SQL injection vulnerability found: {match.group(0)}",
                    location=f"{file_path}:{content[:match.start()].count('\n') + 1}",
                    recommendation="Use parameterized queries or ORM",
                    cwe_id=self.known_vulnerabilities["sql_injection"]["cwe_id"],
                    cvss_score=self.known_vulnerabilities["sql_injection"]["cvss_score"]
                ))

        return issues

    def _check_xss(self, content: str, file_path: str) -> List[SecurityIssue]:
        """Check for XSS vulnerabilities"""
        issues = []

        for pattern in self.known_vulnerabilities["xss"]["patterns"]:
            matches = re.finditer(pattern, content)
            for match in matches:
                issues.append(SecurityIssue(
                    type="xss",
                    severity="high",
                    description=f"Potential XSS vulnerability found: {match.group(0)}",
                    location=f"{file_path}:{content[:match.start()].count('\n') + 1}",
                    recommendation="Implement proper input validation and output encoding",
                    cwe_id=self.known_vulnerabilities["xss"]["cwe_id"],
                    cvss_score=self.known_vulnerabilities["xss"]["cvss_score"]
                ))

        return issues

    def _check_csrf(self, content: str, file_path: str) -> List[SecurityIssue]:
        """Check for CSRF vulnerabilities"""
        issues = []

        for pattern in self.known_vulnerabilities["csrf"]["patterns"]:
            matches = re.finditer(pattern, content)
            for match in matches:
                issues.append(SecurityIssue(
                    type="csrf",
                    severity="high",
                    description=f"Potential CSRF vulnerability found: {match.group(0)}",
                    location=f"{file_path}:{content[:match.start()].count('\n') + 1}",
                    recommendation="Implement CSRF tokens and validate requests",
                    cwe_id=self.known_vulnerabilities["csrf"]["cwe_id"],
                    cvss_score=self.known_vulnerabilities["csrf"]["cvss_score"]
                ))

        return issues

    def _analyze_ast(self, tree: ast.AST, file_path: str) -> List[SecurityIssue]:
        """Analyze AST for security issues"""
        issues = []

        class SecurityVisitor(ast.NodeVisitor):
            def __init__(self, file_path: str):
                self.file_path = file_path
                self.issues = []

            def visit_Call(self, node: ast.Call):
                # Check for dangerous function calls
                if isinstance(node.func, ast.Name):
                    if node.func.id in ["eval", "exec", "os.system", "subprocess.call"]:
                        self.issues.append(SecurityIssue(
                            type="dangerous_function",
                            severity="critical",
                            description=f"Dangerous function call: {node.func.id}",
                            location=f"{self.file_path}:{node.lineno}",
                            recommendation="Avoid using dangerous functions, use safer alternatives",
                            cwe_id="CWE-78",
                            cvss_score=9.8
                        ))

                self.generic_visit(node)

        visitor = SecurityVisitor(file_path)
        visitor.visit(tree)
        issues.extend(visitor.issues)

        return issues

    async def _simulate_attack(self, vector: str, level: str, component: str, file_path: str) -> Optional[SecurityIssue]:
        """Simulate a specific security attack"""
        try:
            # Implement attack simulation logic
            # This would involve actually attempting the attack in a controlled environment
            pass
        except Exception as e:
            logger.error(f"Error simulating {vector} attack: {e}")
            return None

    def calculate_security_score(self, issues: List[SecurityIssue]) -> float:
        """Calculate security score based on issues found"""
        if not issues:
            return 100.0

        # Weight issues by severity
        severity_weights = {
            "critical": 1.0,
            "high": 0.8,
            "medium": 0.5,
            "low": 0.2
        }

        total_weight = sum(severity_weights.get(issue.severity, 0.5) for issue in issues)
        max_possible_weight = len(issues) * 1.0  # Assuming all issues are critical

        return max(0.0, 100.0 * (1.0 - total_weight / max_possible_weight))

async def main():
    """Main function"""
    try:
        sniffer = SecuritySniffer()
        issues = await sniffer.sniff_file("example.py")
        score = sniffer.calculate_security_score(issues)
        print(f"Security score: {score}")
        for issue in issues:
            print(f"Issue: {issue}")
    except Exception as e:
        logger.error(f"Security sniffing failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
