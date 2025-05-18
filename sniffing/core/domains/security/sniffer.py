"""
Security sniffer for vulnerability detection and compliance checking.
"""
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from ...base.sniffer import BaseSniffer
from ...utils.config import SnifferConfig
from ...utils.logging import setup_logger

logger = logging.getLogger("security_sniffer")

class SecuritySniffer(BaseSniffer):
    """Sniffer for security testing."""

    def __init__(self, config: SnifferConfig):
        """Initialize security sniffer.

        Args:
            config: Sniffer configuration
        """
        super().__init__("security", config)
        self.vulnerability_patterns = self._load_vulnerability_patterns()
        self.compliance_rules = self._load_compliance_rules()
        self.attack_simulations = self._load_attack_simulations()

    def _load_vulnerability_patterns(self) -> Dict[str, Any]:
        """Load vulnerability patterns.

        Returns:
            Dictionary of vulnerability patterns
        """
        try:
            patterns = self.config.get_sniffer_config("security").get(
                "vulnerability_patterns",
                {}
            )
            if not patterns:
                logger.warning("No vulnerability patterns configured")
            return patterns

        except Exception as e:
            logger.error(f"Error loading vulnerability patterns: {e}")
            return {}

    def _load_compliance_rules(self) -> Dict[str, Any]:
        """Load compliance rules.

        Returns:
            Dictionary of compliance rules
        """
        try:
            rules = self.config.get_sniffer_config("security").get(
                "compliance_rules",
                {}
            )
            if not rules:
                logger.warning("No compliance rules configured")
            return rules

        except Exception as e:
            logger.error(f"Error loading compliance rules: {e}")
            return {}

    def _load_attack_simulations(self) -> Dict[str, Any]:
        """Load attack simulations.

        Returns:
            Dictionary of attack simulations
        """
        try:
            simulations = self.config.get_sniffer_config("security").get(
                "attack_simulations",
                {}
            )
            if not simulations:
                logger.warning("No attack simulations configured")
            return simulations

        except Exception as e:
            logger.error(f"Error loading attack simulations: {e}")
            return {}

    async def _sniff_files(self, files: List[str]) -> Dict[str, Any]:
        """Run security sniffing.

        Args:
            files: Files to sniff

        Returns:
            Sniffing results
        """
        try:
            results = {
                "status": "running",
                "timestamp": datetime.now(),
                "files": files,
                "issues": [],
                "coverage": {}
            }

            # Run vulnerability scan
            vulnerability_results = await self._scan_vulnerabilities(files)
            results["vulnerabilities"] = vulnerability_results

            # Check compliance
            compliance_results = await self._check_compliance(files)
            results["compliance"] = compliance_results

            # Run attack simulations
            simulation_results = await self._simulate_attacks(files)
            results["simulations"] = simulation_results

            # Calculate coverage
            coverage = await self._calculate_security_coverage(
                files,
                vulnerability_results,
                compliance_results,
                simulation_results
            )
            results["coverage"] = coverage

            # Aggregate issues
            issues = []
            issues.extend(vulnerability_results.get("issues", []))
            issues.extend(compliance_results.get("issues", []))
            issues.extend(simulation_results.get("issues", []))
            results["issues"] = issues

            # Update status
            results["status"] = "completed"

            return results

        except Exception as e:
            logger.error(f"Error running security sniffing: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now()
            }

    async def _scan_vulnerabilities(
        self,
        files: List[str]
    ) -> Dict[str, Any]:
        """Scan for vulnerabilities.

        Args:
            files: Files to scan

        Returns:
            Vulnerability scan results
        """
        try:
            results = {
                "status": "running",
                "timestamp": datetime.now(),
                "files": files,
                "issues": []
            }

            for file in files:
                # Scan file
                file_results = await self._scan_file_vulnerabilities(file)
                results["issues"].extend(file_results.get("issues", []))

            # Update status
            results["status"] = "completed"

            return results

        except Exception as e:
            logger.error(f"Error scanning vulnerabilities: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now()
            }

    async def _scan_file_vulnerabilities(
        self,
        file: str
    ) -> Dict[str, Any]:
        """Scan file for vulnerabilities.

        Args:
            file: File to scan

        Returns:
            File vulnerability results
        """
        try:
            results = {
                "file": file,
                "issues": []
            }

            # Read file content
            with open(file, "r") as f:
                content = f.read()

            # Check each pattern
            for pattern_id, pattern in self.vulnerability_patterns.items():
                matches = await self._check_vulnerability_pattern(
                    content,
                    pattern
                )
                if matches:
                    results["issues"].extend([
                        {
                            "id": f"VUL-{pattern_id}-{i}",
                            "type": "vulnerability",
                            "pattern": pattern_id,
                            "severity": pattern.get("severity", "medium"),
                            "description": pattern.get("description", ""),
                            "line": match.get("line"),
                            "code": match.get("code"),
                            "fix": pattern.get("fix", "")
                        }
                        for i, match in enumerate(matches)
                    ])

            return results

        except Exception as e:
            logger.error(f"Error scanning file {file}: {e}")
            return {
                "file": file,
                "error": str(e)
            }

    async def _check_vulnerability_pattern(
        self,
        content: str,
        pattern: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Check content for vulnerability pattern.

        Args:
            content: Content to check
            pattern: Pattern to check for

        Returns:
            List of pattern matches
        """
        try:
            matches = []
            lines = content.split("\n")

            for i, line in enumerate(lines):
                if pattern.get("regex"):
                    # Use regex pattern
                    import re
                    if re.search(pattern["regex"], line):
                        matches.append({
                            "line": i + 1,
                            "code": line.strip()
                        })
                elif pattern.get("ast"):
                    # Use AST pattern
                    import ast
                    try:
                        tree = ast.parse(line)
                        if self._check_ast_pattern(tree, pattern["ast"]):
                            matches.append({
                                "line": i + 1,
                                "code": line.strip()
                            })
                    except:
                        pass

            return matches

        except Exception as e:
            logger.error(f"Error checking pattern: {e}")
            return []

    async def _check_compliance(
        self,
        files: List[str]
    ) -> Dict[str, Any]:
        """Check compliance rules.

        Args:
            files: Files to check

        Returns:
            Compliance check results
        """
        try:
            results = {
                "status": "running",
                "timestamp": datetime.now(),
                "files": files,
                "issues": []
            }

            for file in files:
                # Check file
                file_results = await self._check_file_compliance(file)
                results["issues"].extend(file_results.get("issues", []))

            # Update status
            results["status"] = "completed"

            return results

        except Exception as e:
            logger.error(f"Error checking compliance: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now()
            }

    async def _check_file_compliance(
        self,
        file: str
    ) -> Dict[str, Any]:
        """Check file compliance.

        Args:
            file: File to check

        Returns:
            File compliance results
        """
        try:
            results = {
                "file": file,
                "issues": []
            }

            # Read file content
            with open(file, "r") as f:
                content = f.read()

            # Check each rule
            for rule_id, rule in self.compliance_rules.items():
                violations = await self._check_compliance_rule(
                    content,
                    rule
                )
                if violations:
                    results["issues"].extend([
                        {
                            "id": f"COM-{rule_id}-{i}",
                            "type": "compliance",
                            "rule": rule_id,
                            "severity": rule.get("severity", "medium"),
                            "description": rule.get("description", ""),
                            "line": violation.get("line"),
                            "code": violation.get("code"),
                            "fix": rule.get("fix", "")
                        }
                        for i, violation in enumerate(violations)
                    ])

            return results

        except Exception as e:
            logger.error(f"Error checking file {file}: {e}")
            return {
                "file": file,
                "error": str(e)
            }

    async def _check_compliance_rule(
        self,
        content: str,
        rule: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Check content for compliance rule.

        Args:
            content: Content to check
            rule: Rule to check for

        Returns:
            List of rule violations
        """
        try:
            violations = []
            lines = content.split("\n")

            for i, line in enumerate(lines):
                if rule.get("regex"):
                    # Use regex pattern
                    import re
                    if re.search(rule["regex"], line):
                        violations.append({
                            "line": i + 1,
                            "code": line.strip()
                        })

            return violations

        except Exception as e:
            logger.error(f"Error checking rule: {e}")
            return []

    async def _simulate_attacks(
        self,
        files: List[str]
    ) -> Dict[str, Any]:
        """Run attack simulations.

        Args:
            files: Files to test

        Returns:
            Attack simulation results
        """
        try:
            results = {
                "status": "running",
                "timestamp": datetime.now(),
                "files": files,
                "issues": []
            }

            for file in files:
                # Run simulations
                file_results = await self._simulate_file_attacks(file)
                results["issues"].extend(file_results.get("issues", []))

            # Update status
            results["status"] = "completed"

            return results

        except Exception as e:
            logger.error(f"Error simulating attacks: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now()
            }

    async def _simulate_file_attacks(
        self,
        file: str
    ) -> Dict[str, Any]:
        """Run attack simulations on file.

        Args:
            file: File to test

        Returns:
            File simulation results
        """
        try:
            results = {
                "file": file,
                "issues": []
            }

            # Read file content
            with open(file, "r") as f:
                content = f.read()

            # Run each simulation
            for sim_id, simulation in self.attack_simulations.items():
                findings = await self._run_attack_simulation(
                    content,
                    simulation
                )
                if findings:
                    results["issues"].extend([
                        {
                            "id": f"SIM-{sim_id}-{i}",
                            "type": "simulation",
                            "simulation": sim_id,
                            "severity": simulation.get("severity", "medium"),
                            "description": simulation.get("description", ""),
                            "line": finding.get("line"),
                            "code": finding.get("code"),
                            "fix": simulation.get("fix", "")
                        }
                        for i, finding in enumerate(findings)
                    ])

            return results

        except Exception as e:
            logger.error(f"Error simulating file {file}: {e}")
            return {
                "file": file,
                "error": str(e)
            }

    async def _run_attack_simulation(
        self,
        content: str,
        simulation: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Run attack simulation on content.

        Args:
            content: Content to test
            simulation: Simulation to run

        Returns:
            List of simulation findings
        """
        try:
            findings = []
            lines = content.split("\n")

            for i, line in enumerate(lines):
                if simulation.get("regex"):
                    # Use regex pattern
                    import re
                    if re.search(simulation["regex"], line):
                        findings.append({
                            "line": i + 1,
                            "code": line.strip()
                        })
                elif simulation.get("ast"):
                    # Use AST pattern
                    import ast
                    try:
                        tree = ast.parse(line)
                        if self._check_ast_pattern(tree, simulation["ast"]):
                            findings.append({
                                "line": i + 1,
                                "code": line.strip()
                            })
                    except:
                        pass

            return findings

        except Exception as e:
            logger.error(f"Error running simulation: {e}")
            return []

    def _check_ast_pattern(
        self,
        tree: Any,
        pattern: Dict[str, Any]
    ) -> bool:
        """Check AST for pattern.

        Args:
            tree: AST to check
            pattern: Pattern to check for

        Returns:
            Whether pattern matches
        """
        try:
            import ast

            class PatternVisitor(ast.NodeVisitor):
                def __init__(self, pattern):
                    self.pattern = pattern
                    self.matches = False

                def visit(self, node):
                    if isinstance(node, getattr(ast, self.pattern["type"])):
                        if all(
                            hasattr(node, attr) and
                            getattr(node, attr) == value
                            for attr, value in self.pattern.get("attributes", {}).items()
                        ):
                            self.matches = True
                    self.generic_visit(node)

            visitor = PatternVisitor(pattern)
            visitor.visit(tree)
            return visitor.matches

        except Exception as e:
            logger.error(f"Error checking AST pattern: {e}")
            return False

    async def _calculate_security_coverage(
        self,
        files: List[str],
        vulnerability_results: Dict[str, Any],
        compliance_results: Dict[str, Any],
        simulation_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate security coverage.

        Args:
            files: Files tested
            vulnerability_results: Vulnerability scan results
            compliance_results: Compliance check results
            simulation_results: Attack simulation results

        Returns:
            Coverage metrics
        """
        try:
            # Count total lines
            total_lines = 0
            for file in files:
                with open(file, "r") as f:
                    total_lines += sum(1 for _ in f)

            # Count covered lines
            covered_lines = set()
            for results in [
                vulnerability_results,
                compliance_results,
                simulation_results
            ]:
                for issue in results.get("issues", []):
                    if "line" in issue:
                        covered_lines.add(issue["line"])

            return {
                "total_lines": total_lines,
                "covered_lines": len(covered_lines),
                "coverage_percent": (
                    len(covered_lines) / total_lines * 100
                    if total_lines > 0 else 0
                )
            }

        except Exception as e:
            logger.error(f"Error calculating coverage: {e}")
            return {
                "total_lines": 0,
                "covered_lines": 0,
                "coverage_percent": 0
            }
