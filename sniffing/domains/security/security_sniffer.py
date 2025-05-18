"""
Enhanced security sniffer for detecting vulnerabilities, compliance issues, and simulating attacks.
"""
import ast
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from ...core.base.base_sniffer import BaseSniffer
from ...core.utils.result import SniffingResult

logger = logging.getLogger("security_sniffer")

class SecuritySniffer(BaseSniffer):
    """Enhanced sniffer for security testing and compliance validation."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize security sniffer.

        Args:
            config: Configuration dictionary for the sniffer
        """
        super().__init__(config)
        self.vulnerability_patterns = self._load_vulnerability_patterns()
        self.compliance_checks = self._load_compliance_checks()
        self.attack_simulations = self._load_attack_simulations()
        self.soc2_requirements = self._load_soc2_requirements()
        self.ai_security_model = self._load_ai_security_model()

    def get_sniffer_type(self) -> str:
        """Return the type of this sniffer."""
        return "security"

    async def _sniff_file_impl(self, file: str) -> SniffingResult:
        """Implementation of file sniffing logic.

        Args:
            file: Path to the file to sniff.

        Returns:
            SniffingResult object
        """
        try:
            # Create result
            result = SniffingResult(file, self.get_sniffer_type())

            # Read file content
            with open(file, "r") as f:
                content = f.read()

            # Run security checks
            await self._check_vulnerabilities(content, result)
            await self._check_compliance(content, result)
            await self._simulate_attacks(content, result)
            await self._validate_soc2(content, result)
            await self._run_ai_security_analysis(content, result)

            # Update status
            result.status = not result.has_critical_issues()

            return result

        except Exception as e:
            logger.error(f"Error sniffing file {file}: {e}")
            return SniffingResult(file, self.get_sniffer_type(), status=False)

    def _load_vulnerability_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Load vulnerability detection patterns."""
        return {
            "sql_injection": {
                "pattern": r".*\b(SELECT|INSERT|UPDATE|DELETE)\b.*\+.*",
                "severity": "critical",
                "description": "Potential SQL injection vulnerability",
                "cwe": "CWE-89",
                "fix_template": "Use parameterized queries or an ORM",
                "soc2_control": "CC6.1"
            },
            "xss": {
                "pattern": r".*innerHTML.*=.*|.*document\.write\(.*\)",
                "severity": "critical",
                "description": "Potential XSS vulnerability",
                "cwe": "CWE-79",
                "fix_template": "Use safe DOM manipulation methods or sanitize input",
                "soc2_control": "CC6.6"
            },
            "command_injection": {
                "pattern": r".*exec\(.*\)|.*eval\(.*\)|.*system\(.*\)",
                "severity": "critical",
                "description": "Potential command injection vulnerability",
                "cwe": "CWE-78",
                "fix_template": "Use safe command execution methods or validate input",
                "soc2_control": "CC6.1"
            },
            "hardcoded_credentials": {
                "pattern": r"password\s*=\s*['\"][^'\"]+['\"]|api_key\s*=\s*['\"][^'\"]+['\"]",
                "severity": "high",
                "description": "Hardcoded credentials detected",
                "cwe": "CWE-798",
                "fix_template": "Use environment variables or secure credential storage",
                "soc2_control": "CC6.1"
            },
            "insecure_crypto": {
                "pattern": r".*MD5|.*SHA1",
                "severity": "high",
                "description": "Use of insecure cryptographic algorithms",
                "cwe": "CWE-327",
                "fix_template": "Use strong cryptographic algorithms (e.g., SHA-256, bcrypt)",
                "soc2_control": "CC6.7"
            },
            "path_traversal": {
                "pattern": r".*\.\./.*|.*\.\.\\.*",
                "severity": "high",
                "description": "Potential path traversal vulnerability",
                "cwe": "CWE-22",
                "fix_template": "Use safe path manipulation methods and validate input",
                "soc2_control": "CC6.1"
            },
            "insecure_deserialization": {
                "pattern": r".*pickle\.loads?\(.*\)|.*yaml\.load\(.*\)",
                "severity": "high",
                "description": "Potential insecure deserialization",
                "cwe": "CWE-502",
                "fix_template": "Use safe deserialization methods or validate input",
                "soc2_control": "CC6.6"
            }
        }

    def _load_compliance_checks(self) -> Dict[str, Dict[str, Any]]:
        """Load compliance check patterns."""
        return {
            "logging": {
                "pattern": r".*\blog\b.*",
                "requirement": "SOC2-LOG",
                "description": "Logging implementation",
                "severity": "medium",
                "soc2_control": "CC7.2"
            },
            "authentication": {
                "pattern": r".*\b(auth|login|authenticate)\b.*",
                "requirement": "SOC2-AUTH",
                "description": "Authentication implementation",
                "severity": "high",
                "soc2_control": "CC6.1"
            },
            "encryption": {
                "pattern": r".*\b(encrypt|decrypt)\b.*",
                "requirement": "SOC2-ENC",
                "description": "Encryption implementation",
                "severity": "high",
                "soc2_control": "CC6.7"
            },
            "access_control": {
                "pattern": r".*\b(permission|role|access)\b.*",
                "requirement": "SOC2-ACC",
                "description": "Access control implementation",
                "severity": "high",
                "soc2_control": "CC6.3"
            },
            "audit": {
                "pattern": r".*\b(audit|track|monitor)\b.*",
                "requirement": "SOC2-AUD",
                "description": "Audit trail implementation",
                "severity": "medium",
                "soc2_control": "CC7.2"
            }
        }

    def _load_attack_simulations(self) -> Dict[str, Dict[str, Any]]:
        """Load attack simulation patterns."""
        return {
            "injection": {
                "payloads": [
                    "' OR '1'='1",
                    "'; DROP TABLE users; --",
                    "<script>alert('xss')</script>",
                    "$(cat /etc/passwd)"
                ],
                "severity": "critical",
                "description": "Injection attack simulation",
                "soc2_control": "CC6.1"
            },
            "authentication_bypass": {
                "payloads": [
                    "admin' --",
                    "' OR '1'='1' --",
                    "' UNION SELECT NULL,NULL,NULL --"
                ],
                "severity": "critical",
                "description": "Authentication bypass simulation",
                "soc2_control": "CC6.1"
            },
            "path_traversal": {
                "payloads": [
                    "../../../etc/passwd",
                    "..\\..\\..\\windows\\system32\\config\\sam",
                    "%2e%2e%2f%2e%2e%2f"
                ],
                "severity": "high",
                "description": "Path traversal simulation",
                "soc2_control": "CC6.1"
            }
        }

    def _load_soc2_requirements(self) -> Dict[str, Dict[str, Any]]:
        """Load SOC2 compliance requirements."""
        return {
            "CC6.1": {
                "title": "Secure Software Development",
                "description": "The entity implements logical access security software, infrastructure, and architectures over protected information assets to protect them from security events.",
                "checks": [
                    "vulnerability_scanning",
                    "secure_coding",
                    "access_control"
                ]
            },
            "CC6.3": {
                "title": "Access Control",
                "description": "The entity implements logical access security software, infrastructure, and architectures over protected information assets to protect them from security events.",
                "checks": [
                    "authentication",
                    "authorization",
                    "role_based_access"
                ]
            },
            "CC6.6": {
                "title": "Secure Input and Output",
                "description": "The entity implements input and output controls.",
                "checks": [
                    "input_validation",
                    "output_encoding",
                    "sanitization"
                ]
            },
            "CC6.7": {
                "title": "Cryptographic Controls",
                "description": "The entity restricts the transmission, movement, and removal of information to authorized internal and external users and processes, and protects it during transmission, movement, or removal to meet the entity's objectives.",
                "checks": [
                    "encryption_in_transit",
                    "encryption_at_rest",
                    "key_management"
                ]
            },
            "CC7.2": {
                "title": "Security Event Monitoring",
                "description": "The entity monitors system components and the operation of those components for anomalies that are indicative of malicious acts, natural disasters, and errors affecting the entity's ability to meet its objectives.",
                "checks": [
                    "logging",
                    "monitoring",
                    "alerting"
                ]
            }
        }

    def _load_ai_security_model(self) -> Any:
        """Load AI security analysis model."""
        try:
            return self.ai_analyzer.load_security_model()
        except Exception as e:
            logger.error(f"Error loading AI security model: {e}")
            return None

    async def _check_vulnerabilities(self, content: str, result: SniffingResult) -> None:
        """Check for security vulnerabilities.

        Args:
            content: File content to check
            result: SniffingResult to update
        """
        try:
            for vuln_type, vuln_info in self.vulnerability_patterns.items():
                matches = re.finditer(vuln_info["pattern"], content, re.MULTILINE)
                for match in matches:
                    issue = {
                        "type": "vulnerability",
                        "subtype": vuln_type,
                        "severity": vuln_info["severity"],
                        "description": vuln_info["description"],
                        "line": content.count("\n", 0, match.start()) + 1,
                        "code": match.group(0).strip(),
                        "cwe": vuln_info.get("cwe"),
                        "fix_suggestion": vuln_info.get("fix_template"),
                        "soc2_control": vuln_info.get("soc2_control")
                    }
                    result.add_issue(issue)

            # Run AI vulnerability detection
            if self.ai_security_model:
                ai_vulns = await self.ai_analyzer.detect_vulnerabilities(
                    content,
                    self.ai_security_model
                )
                for vuln in ai_vulns:
                    result.add_issue(vuln)

        except Exception as e:
            logger.error(f"Error checking vulnerabilities: {e}")

    async def _check_compliance(self, content: str, result: SniffingResult) -> None:
        """Check for compliance issues.

        Args:
            content: File content to check
            result: SniffingResult to update
        """
        try:
            for check_type, check_info in self.compliance_checks.items():
                matches = re.finditer(check_info["pattern"], content, re.MULTILINE)
                implementations = list(matches)

                if not implementations:
                    issue = {
                        "type": "compliance",
                        "subtype": check_type,
                        "severity": check_info["severity"],
                        "description": f"Missing {check_info['description']}",
                        "requirement": check_info["requirement"],
                        "soc2_control": check_info.get("soc2_control")
                    }
                    result.add_issue(issue)
                else:
                    # Add metric for implementation
                    result.update_metrics({
                        f"compliance_{check_type}_implementations": len(implementations)
                    })

            # Run AI compliance checks
            if self.ai_security_model:
                ai_compliance = await self.ai_analyzer.check_compliance(
                    content,
                    self.ai_security_model
                )
                for issue in ai_compliance:
                    result.add_issue(issue)

        except Exception as e:
            logger.error(f"Error checking compliance: {e}")

    async def _simulate_attacks(self, content: str, result: SniffingResult) -> None:
        """Simulate attacks to detect vulnerabilities.

        Args:
            content: File content to check
            result: SniffingResult to update
        """
        try:
            for attack_type, attack_info in self.attack_simulations.items():
                for payload in attack_info["payloads"]:
                    # Check if code is vulnerable to payload
                    if await self._is_vulnerable_to_payload(content, payload):
                        issue = {
                            "type": "attack_simulation",
                            "subtype": attack_type,
                            "severity": attack_info["severity"],
                            "description": attack_info["description"],
                            "payload": payload,
                            "soc2_control": attack_info.get("soc2_control")
                        }
                        result.add_issue(issue)

            # Run AI attack simulations
            if self.ai_security_model:
                ai_attacks = await self.ai_analyzer.simulate_attacks(
                    content,
                    self.ai_security_model
                )
                for attack in ai_attacks:
                    result.add_issue(attack)

        except Exception as e:
            logger.error(f"Error simulating attacks: {e}")

    async def _validate_soc2(self, content: str, result: SniffingResult) -> None:
        """Validate SOC2 compliance requirements.

        Args:
            content: File content to check
            result: SniffingResult to update
        """
        try:
            for control_id, control_info in self.soc2_requirements.items():
                # Check each required control
                for check in control_info["checks"]:
                    if not await self._validate_soc2_control(content, check):
                        issue = {
                            "type": "soc2",
                            "subtype": check,
                            "severity": "high",
                            "description": f"Missing SOC2 control: {check}",
                            "control_id": control_id,
                            "control_title": control_info["title"],
                            "control_description": control_info["description"]
                        }
                        result.add_issue(issue)

            # Run AI SOC2 validation
            if self.ai_security_model:
                ai_soc2 = await self.ai_analyzer.validate_soc2(
                    content,
                    self.ai_security_model
                )
                for issue in ai_soc2:
                    result.add_issue(issue)

        except Exception as e:
            logger.error(f"Error validating SOC2 compliance: {e}")

    async def _run_ai_security_analysis(self, content: str, result: SniffingResult) -> None:
        """Run AI-powered security analysis.

        Args:
            content: File content to analyze
            result: SniffingResult to update
        """
        try:
            if self.ai_security_model:
                # Run comprehensive AI analysis
                analysis = await self.ai_analyzer.analyze_security(
                    content,
                    self.ai_security_model
                )

                # Add issues from AI analysis
                for issue in analysis.get("issues", []):
                    result.add_issue(issue)

                # Update metrics
                result.update_metrics({
                    "ai_security_analysis": {
                        "confidence": analysis.get("confidence", 0.0),
                        "risk_score": analysis.get("risk_score", 0.0),
                        "compliance_score": analysis.get("compliance_score", 0.0)
                    }
                })

        except Exception as e:
            logger.error(f"Error running AI security analysis: {e}")

    async def _is_vulnerable_to_payload(self, content: str, payload: str) -> bool:
        """Check if code is vulnerable to attack payload.

        Args:
            content: File content to check
            payload: Attack payload to test

        Returns:
            True if vulnerable, False otherwise
        """
        try:
            # Parse code into AST
            tree = ast.parse(content)

            # Look for vulnerable patterns
            for node in ast.walk(tree):
                # Check for direct string concatenation
                if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
                    return True

                # Check for string formatting
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                    if node.func.attr in ["format", "replace"]:
                        return True

                # Check for exec/eval
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                    if node.func.id in ["exec", "eval"]:
                        return True

            return False

        except Exception as e:
            logger.error(f"Error checking payload vulnerability: {e}")
            return False

    async def _validate_soc2_control(self, content: str, control: str) -> bool:
        """Validate a specific SOC2 control.

        Args:
            content: File content to check
            control: Control to validate

        Returns:
            True if control is implemented, False otherwise
        """
        try:
            # Check for control implementation patterns
            patterns = {
                "vulnerability_scanning": r".*scan.*vuln.*|.*security.*check.*",
                "secure_coding": r".*sanitize.*|.*validate.*|.*escape.*",
                "access_control": r".*auth.*|.*permission.*|.*role.*",
                "authentication": r".*login.*|.*authenticate.*|.*session.*",
                "authorization": r".*authorize.*|.*permission.*|.*role.*",
                "role_based_access": r".*role.*|.*permission.*|.*access.*",
                "input_validation": r".*validate.*|.*sanitize.*|.*check.*input.*",
                "output_encoding": r".*encode.*|.*escape.*|.*sanitize.*output.*",
                "sanitization": r".*sanitize.*|.*clean.*|.*escape.*",
                "encryption_in_transit": r".*ssl.*|.*tls.*|.*https.*",
                "encryption_at_rest": r".*encrypt.*|.*cipher.*|.*crypt.*",
                "key_management": r".*key.*manage.*|.*secret.*|.*credential.*",
                "logging": r".*log\.|.*logger.*|.*audit.*",
                "monitoring": r".*monitor.*|.*watch.*|.*track.*",
                "alerting": r".*alert.*|.*notify.*|.*warn.*"
            }

            if control in patterns:
                return bool(re.search(patterns[control], content, re.IGNORECASE))

            return False

        except Exception as e:
            logger.error(f"Error validating SOC2 control: {e}")
            return False

    async def _apply_fixes(self, suggestions: List[Dict[str, Any]]) -> bool:
        """Apply fix suggestions to issues.

        Args:
            suggestions: List of fix suggestions from AI

        Returns:
            True if all fixes were applied successfully, False otherwise
        """
        try:
            success = True
            for suggestion in suggestions:
                # Get file content
                with open(suggestion["file"], "r") as f:
                    content = f.read()

                # Apply fix
                if suggestion.get("fix_type") == "replace":
                    content = content.replace(
                        suggestion["old_code"],
                        suggestion["new_code"]
                    )
                elif suggestion.get("fix_type") == "insert":
                    lines = content.splitlines()
                    lines.insert(
                        suggestion["line"] - 1,
                        suggestion["code"]
                    )
                    content = "\n".join(lines)
                else:
                    logger.warning(f"Unknown fix type: {suggestion.get('fix_type')}")
                    success = False
                    continue

                # Write fixed content
                with open(suggestion["file"], "w") as f:
                    f.write(content)

                # Validate fix
                if not await self._validate_fix(suggestion, content):
                    success = False

            return success

        except Exception as e:
            logger.error(f"Error applying fixes: {e}")
            return False

    async def _validate_fix(self, suggestion: Dict[str, Any], content: str) -> bool:
        """Validate that a fix was successful.

        Args:
            suggestion: Fix suggestion that was applied
            content: Updated file content

        Returns:
            True if fix was successful, False otherwise
        """
        try:
            # Create temporary result
            result = SniffingResult(suggestion["file"], self.get_sniffer_type())

            # Run security checks on updated content
            await self._check_vulnerabilities(content, result)
            await self._check_compliance(content, result)
            await self._simulate_attacks(content, result)
            await self._validate_soc2(content, result)

            # Check if original issue was fixed
            for issue in result.issues:
                if (
                    issue["type"] == suggestion.get("issue_type") and
                    issue["subtype"] == suggestion.get("issue_subtype")
                ):
                    return False

            return True

        except Exception as e:
            logger.error(f"Error validating fix: {e}")
            return False
