"""
Security domain sniffer for vulnerability detection and compliance checking.
"""
import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from ....utils.config import MCPConfig
from ....utils.logging import setup_logger
from ..base import BaseSniffer

logger = logging.getLogger("security_sniffer")

class SecuritySniffer(BaseSniffer):
    """Security domain sniffer."""

    def __init__(self, config: MCPConfig):
        """Initialize security sniffer.

        Args:
            config: MCP configuration
        """
        super().__init__(config, "security")
        self.patterns = self._load_patterns()
        self.rules = self._load_rules()
        self.simulations = self._load_simulations()

    def _load_patterns(self) -> Dict[str, Any]:
        """Load security patterns.

        Returns:
            Pattern dictionary
        """
        try:
            patterns_path = Path(self.config.domains["security"]["patterns_path"])
            if not patterns_path.exists():
                return {}

            # Load patterns
            import yaml
            patterns = {}
            for pattern_file in patterns_path.glob("*.yaml"):
                with open(pattern_file) as f:
                    patterns[pattern_file.stem] = yaml.safe_load(f)

            return patterns

        except Exception as e:
            logger.error(f"Error loading security patterns: {e}")
            return {}

    def _load_rules(self) -> Dict[str, Any]:
        """Load security rules.

        Returns:
            Rules dictionary
        """
        try:
            rules_path = Path(self.config.domains["security"]["rules_path"])
            if not rules_path.exists():
                return {}

            # Load rules
            import yaml
            rules = {}
            for rule_file in rules_path.glob("*.yaml"):
                with open(rule_file) as f:
                    rules[rule_file.stem] = yaml.safe_load(f)

            return rules

        except Exception as e:
            logger.error(f"Error loading security rules: {e}")
            return {}

    def _load_simulations(self) -> Dict[str, Any]:
        """Load security simulations.

        Returns:
            Simulations dictionary
        """
        try:
            simulations_path = Path(self.config.domains["security"]["simulations_path"])
            if not simulations_path.exists():
                return {}

            # Load simulations
            import yaml
            simulations = {}
            for simulation_file in simulations_path.glob("*.yaml"):
                with open(simulation_file) as f:
                    simulations[simulation_file.stem] = yaml.safe_load(f)

            return simulations

        except Exception as e:
            logger.error(f"Error loading security simulations: {e}")
            return {}

    async def sniff_file(self, file: str) -> Dict[str, Any]:
        """Sniff file for security issues.

        Args:
            file: File to sniff

        Returns:
            Sniffing results
        """
        try:
            results = {
                "status": "running",
                "file": file,
                "timestamp": datetime.now(),
                "issues": [],
                "metrics": {}
            }

            # Read file
            with open(file) as f:
                content = f.read()

            # Run pattern matching
            pattern_issues = await self._check_patterns(content)
            results["issues"].extend(pattern_issues)

            # Run rule validation
            rule_issues = await self._check_rules(content)
            results["issues"].extend(rule_issues)

            # Run simulations
            simulation_issues = await self._run_simulations(file)
            results["issues"].extend(simulation_issues)

            # Calculate metrics
            results["metrics"] = self._calculate_metrics(results["issues"])

            # Update status
            results["status"] = "completed"
            if any(issue["severity"] in ["critical", "high"] for issue in results["issues"]):
                results["status"] = "failed"

            return results

        except Exception as e:
            logger.error(f"Error sniffing file {file}: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now()
            }

    async def analyze_result(
        self,
        file: str,
        result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze security sniffing result.

        Args:
            file: Sniffed file
            result: Sniffing result

        Returns:
            Analysis results
        """
        try:
            analysis = {
                "status": "running",
                "file": file,
                "timestamp": datetime.now(),
                "summary": {},
                "recommendations": []
            }

            # Analyze issues
            issues = result.get("issues", [])
            if issues:
                analysis["summary"] = self._analyze_issues(issues)
                analysis["recommendations"] = self._generate_recommendations(issues)

            # Update status
            analysis["status"] = "completed"
            if analysis["summary"].get("critical", 0) > 0:
                analysis["status"] = "failed"

            return analysis

        except Exception as e:
            logger.error(f"Error analyzing result for {file}: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now()
            }

    async def fix_issues(
        self,
        file: str,
        issues: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Fix security issues.

        Args:
            file: File to fix
            issues: Issues to fix

        Returns:
            Fix results
        """
        try:
            fixes = {
                "status": "running",
                "file": file,
                "timestamp": datetime.now(),
                "applied": [],
                "failed": []
            }

            # Read file
            with open(file) as f:
                content = f.read()

            # Apply fixes
            modified_content = content
            for issue in issues:
                try:
                    # Get fix
                    fix = self._get_fix(issue)
                    if not fix:
                        fixes["failed"].append({
                            "issue": issue,
                            "error": "No fix available"
                        })
                        continue

                    # Apply fix
                    modified_content = self._apply_fix(modified_content, fix)
                    fixes["applied"].append({
                        "issue": issue,
                        "fix": fix
                    })

                except Exception as e:
                    fixes["failed"].append({
                        "issue": issue,
                        "error": str(e)
                    })

            # Write file if fixes applied
            if fixes["applied"]:
                with open(file, "w") as f:
                    f.write(modified_content)

            # Update status
            fixes["status"] = "completed"
            if fixes["failed"]:
                fixes["status"] = "partial"

            return fixes

        except Exception as e:
            logger.error(f"Error fixing issues in {file}: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now()
            }

    async def _check_patterns(self, content: str) -> List[Dict[str, Any]]:
        """Check content against security patterns.

        Args:
            content: File content

        Returns:
            List of pattern issues
        """
        try:
            issues = []

            # Check each pattern
            for pattern_name, pattern in self.patterns.items():
                try:
                    import re
                    matches = re.finditer(pattern["regex"], content)
                    for match in matches:
                        issues.append({
                            "type": "pattern",
                            "name": pattern_name,
                            "severity": pattern.get("severity", "medium"),
                            "description": pattern.get("description", ""),
                            "line": content.count("\n", 0, match.start()) + 1,
                            "match": match.group(0)
                        })

                except Exception as e:
                    logger.error(f"Error checking pattern {pattern_name}: {e}")

            return issues

        except Exception as e:
            logger.error(f"Error checking patterns: {e}")
            return []

    async def _check_rules(self, content: str) -> List[Dict[str, Any]]:
        """Check content against security rules.

        Args:
            content: File content

        Returns:
            List of rule issues
        """
        try:
            issues = []

            # Check each rule
            for rule_name, rule in self.rules.items():
                try:
                    # Get rule checker
                    checker = self._get_rule_checker(rule)
                    if not checker:
                        continue

                    # Run check
                    rule_issues = await checker(content, rule)
                    for issue in rule_issues:
                        issue.update({
                            "type": "rule",
                            "name": rule_name
                        })
                        issues.append(issue)

                except Exception as e:
                    logger.error(f"Error checking rule {rule_name}: {e}")

            return issues

        except Exception as e:
            logger.error(f"Error checking rules: {e}")
            return []

    async def _run_simulations(self, file: str) -> List[Dict[str, Any]]:
        """Run security simulations.

        Args:
            file: File to simulate

        Returns:
            List of simulation issues
        """
        try:
            issues = []

            # Run each simulation
            for simulation_name, simulation in self.simulations.items():
                try:
                    # Get simulator
                    simulator = self._get_simulator(simulation)
                    if not simulator:
                        continue

                    # Run simulation
                    simulation_issues = await simulator(file, simulation)
                    for issue in simulation_issues:
                        issue.update({
                            "type": "simulation",
                            "name": simulation_name
                        })
                        issues.append(issue)

                except Exception as e:
                    logger.error(f"Error running simulation {simulation_name}: {e}")

            return issues

        except Exception as e:
            logger.error(f"Error running simulations: {e}")
            return []

    def _get_rule_checker(self, rule: Dict[str, Any]) -> Optional[Any]:
        """Get rule checker function.

        Args:
            rule: Rule configuration

        Returns:
            Rule checker function or None
        """
        try:
            checker_type = rule.get("type")
            if not checker_type:
                return None

            # Get checker
            if checker_type == "regex":
                return self._check_regex_rule
            elif checker_type == "ast":
                return self._check_ast_rule
            elif checker_type == "custom":
                return self._check_custom_rule

            return None

        except Exception as e:
            logger.error(f"Error getting rule checker: {e}")
            return None

    def _get_simulator(self, simulation: Dict[str, Any]) -> Optional[Any]:
        """Get simulation function.

        Args:
            simulation: Simulation configuration

        Returns:
            Simulation function or None
        """
        try:
            simulator_type = simulation.get("type")
            if not simulator_type:
                return None

            # Get simulator
            if simulator_type == "injection":
                return self._simulate_injection
            elif simulator_type == "xss":
                return self._simulate_xss
            elif simulator_type == "csrf":
                return self._simulate_csrf

            return None

        except Exception as e:
            logger.error(f"Error getting simulator: {e}")
            return None

    def _get_fix(self, issue: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get fix for issue.

        Args:
            issue: Issue to fix

        Returns:
            Fix configuration or None
        """
        try:
            issue_type = issue.get("type")
            if not issue_type:
                return None

            # Get fix
            if issue_type == "pattern":
                return self._get_pattern_fix(issue)
            elif issue_type == "rule":
                return self._get_rule_fix(issue)
            elif issue_type == "simulation":
                return self._get_simulation_fix(issue)

            return None

        except Exception as e:
            logger.error(f"Error getting fix: {e}")
            return None

    def _apply_fix(self, content: str, fix: Dict[str, Any]) -> str:
        """Apply fix to content.

        Args:
            content: File content
            fix: Fix configuration

        Returns:
            Modified content
        """
        try:
            fix_type = fix.get("type")
            if not fix_type:
                return content

            # Apply fix
            if fix_type == "replace":
                return self._apply_replace_fix(content, fix)
            elif fix_type == "insert":
                return self._apply_insert_fix(content, fix)
            elif fix_type == "delete":
                return self._apply_delete_fix(content, fix)

            return content

        except Exception as e:
            logger.error(f"Error applying fix: {e}")
            return content

    def _calculate_metrics(self, issues: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate security metrics.

        Args:
            issues: List of issues

        Returns:
            Metrics dictionary
        """
        try:
            metrics = {
                "total_issues": len(issues),
                "severity_counts": {
                    "critical": 0,
                    "high": 0,
                    "medium": 0,
                    "low": 0,
                    "info": 0
                },
                "type_counts": {
                    "pattern": 0,
                    "rule": 0,
                    "simulation": 0
                }
            }

            # Count issues
            for issue in issues:
                # Count by severity
                severity = issue.get("severity", "info").lower()
                if severity in metrics["severity_counts"]:
                    metrics["severity_counts"][severity] += 1

                # Count by type
                issue_type = issue.get("type")
                if issue_type in metrics["type_counts"]:
                    metrics["type_counts"][issue_type] += 1

            return metrics

        except Exception as e:
            logger.error(f"Error calculating metrics: {e}")
            return {}

    def _analyze_issues(self, issues: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze security issues.

        Args:
            issues: List of issues

        Returns:
            Analysis summary
        """
        try:
            summary = {
                "total": len(issues),
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0,
                "info": 0,
                "categories": {}
            }

            # Analyze issues
            for issue in issues:
                # Count by severity
                severity = issue.get("severity", "info").lower()
                if severity in summary:
                    summary[severity] += 1

                # Count by category
                category = issue.get("category", "other")
                if category not in summary["categories"]:
                    summary["categories"][category] = 0
                summary["categories"][category] += 1

            return summary

        except Exception as e:
            logger.error(f"Error analyzing issues: {e}")
            return {}

    def _generate_recommendations(
        self,
        issues: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Generate security recommendations.

        Args:
            issues: List of issues

        Returns:
            List of recommendations
        """
        try:
            recommendations = []

            # Generate recommendations
            for issue in issues:
                try:
                    # Get recommendation
                    recommendation = self._get_recommendation(issue)
                    if recommendation:
                        recommendations.append(recommendation)

                except Exception as e:
                    logger.error(f"Error generating recommendation: {e}")

            return recommendations

        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return []

    def _get_recommendation(self, issue: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get recommendation for issue.

        Args:
            issue: Security issue

        Returns:
            Recommendation or None
        """
        try:
            issue_type = issue.get("type")
            if not issue_type:
                return None

            # Get recommendation
            if issue_type == "pattern":
                return self._get_pattern_recommendation(issue)
            elif issue_type == "rule":
                return self._get_rule_recommendation(issue)
            elif issue_type == "simulation":
                return self._get_simulation_recommendation(issue)

            return None

        except Exception as e:
            logger.error(f"Error getting recommendation: {e}")
            return None
