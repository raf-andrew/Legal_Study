"""
Browser domain sniffer for performance and compatibility analysis.
"""
import asyncio
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import yaml

from ...utils.config import MCPConfig
from ..base import BaseSniffer

logger = logging.getLogger("browser_sniffer")

class BrowserSniffer(BaseSniffer):
    """Browser domain sniffer."""

    def __init__(self, config: MCPConfig):
        """Initialize browser sniffer.

        Args:
            config: MCP configuration
        """
        super().__init__(config, "browser")
        self.patterns = self._load_patterns()
        self.rules = self._load_rules()
        self.simulations = self._load_simulations()

    def _load_patterns(self) -> Dict[str, Any]:
        """Load browser patterns.

        Returns:
            Pattern dictionary
        """
        try:
            patterns_path = Path(self.config.domains["browser"]["patterns_path"])
            if not patterns_path.exists():
                return {}

            # Load patterns
            patterns = {}
            for pattern_file in patterns_path.glob("*.yaml"):
                with open(pattern_file) as f:
                    patterns.update(yaml.safe_load(f))

            return patterns

        except Exception as e:
            logger.error(f"Error loading browser patterns: {e}")
            return {}

    def _load_rules(self) -> Dict[str, Any]:
        """Load browser rules.

        Returns:
            Rules dictionary
        """
        try:
            rules_path = Path(self.config.domains["browser"]["rules_path"])
            if not rules_path.exists():
                return {}

            # Load rules
            rules = {}
            for rule_file in rules_path.glob("*.yaml"):
                with open(rule_file) as f:
                    rules.update(yaml.safe_load(f))

            return rules

        except Exception as e:
            logger.error(f"Error loading browser rules: {e}")
            return {}

    def _load_simulations(self) -> Dict[str, Any]:
        """Load browser simulations.

        Returns:
            Simulations dictionary
        """
        try:
            simulations_path = Path(self.config.domains["browser"]["simulations_path"])
            if not simulations_path.exists():
                return {}

            # Load simulations
            simulations = {}
            for simulation_file in simulations_path.glob("*.yaml"):
                with open(simulation_file) as f:
                    simulations.update(yaml.safe_load(f))

            return simulations

        except Exception as e:
            logger.error(f"Error loading browser simulations: {e}")
            return {}

    async def sniff_file(self, file: str) -> Dict[str, Any]:
        """Sniff file for browser issues.

        Args:
            file: File to sniff

        Returns:
            Sniffing results
        """
        try:
            results = {
                "status": "running",
                "file": file,
                "timestamp": datetime.now().isoformat(),
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
                "timestamp": datetime.now().isoformat()
            }

    async def analyze_result(
        self,
        file: str,
        result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze browser sniffing result.

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
                "timestamp": datetime.now().isoformat(),
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
                "timestamp": datetime.now().isoformat()
            }

    async def fix_issues(
        self,
        file: str,
        issues: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Fix browser issues.

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
                "timestamp": datetime.now().isoformat(),
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
                "timestamp": datetime.now().isoformat()
            }

    async def _check_patterns(self, content: str) -> List[Dict[str, Any]]:
        """Check content against browser patterns.

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
        """Check content against browser rules.

        Args:
            content: File content

        Returns:
            List of rule issues
        """
        try:
            issues = []

            # Check each rule category
            for category_name, category in self.rules.items():
                try:
                    # Get rule checker
                    checker = self._get_rule_checker(category)
                    if not checker:
                        continue

                    # Check rules
                    category_issues = await checker(content, category)
                    for issue in category_issues:
                        issue.update({
                            "type": "rule",
                            "category": category_name
                        })
                        issues.append(issue)

                except Exception as e:
                    logger.error(f"Error checking rules for {category_name}: {e}")

            return issues

        except Exception as e:
            logger.error(f"Error checking rules: {e}")
            return []

    async def _run_simulations(self, file: str) -> List[Dict[str, Any]]:
        """Run browser simulations.

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

    def _get_rule_checker(self, category: Dict[str, Any]) -> Optional[Any]:
        """Get rule checker function.

        Args:
            category: Rule category

        Returns:
            Rule checker function or None
        """
        try:
            category_type = category.get("type")
            if not category_type:
                return None

            # Get checker
            if category_type == "ast":
                return self._check_ast_rules
            elif category_type == "regex":
                return self._check_regex_rules

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
            simulation_type = simulation.get("type")
            if not simulation_type:
                return None

            # Get simulator
            if simulation_type == "performance":
                return self._simulate_performance
            elif simulation_type == "memory":
                return self._simulate_memory
            elif simulation_type == "animation":
                return self._simulate_animation
            elif simulation_type == "layout":
                return self._simulate_layout
            elif simulation_type == "network":
                return self._simulate_network
            elif simulation_type == "compatibility":
                return self._simulate_compatibility
            elif simulation_type == "accessibility":
                return self._simulate_accessibility
            elif simulation_type == "responsive":
                return self._simulate_responsive

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
        """Calculate browser metrics.

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
                },
                "category_counts": {}
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

                # Count by category
                category = issue.get("category", "other")
                if category not in metrics["category_counts"]:
                    metrics["category_counts"][category] = 0
                metrics["category_counts"][category] += 1

            return metrics

        except Exception as e:
            logger.error(f"Error calculating metrics: {e}")
            return {}

    def _analyze_issues(self, issues: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze browser issues.

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
                "categories": {},
                "patterns": {},
                "rules": {},
                "simulations": {}
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

                # Count by type
                issue_type = issue.get("type")
                if issue_type == "pattern":
                    pattern_name = issue.get("name", "unknown")
                    if pattern_name not in summary["patterns"]:
                        summary["patterns"][pattern_name] = 0
                    summary["patterns"][pattern_name] += 1
                elif issue_type == "rule":
                    rule_name = issue.get("name", "unknown")
                    if rule_name not in summary["rules"]:
                        summary["rules"][rule_name] = 0
                    summary["rules"][rule_name] += 1
                elif issue_type == "simulation":
                    simulation_name = issue.get("name", "unknown")
                    if simulation_name not in summary["simulations"]:
                        summary["simulations"][simulation_name] = 0
                    summary["simulations"][simulation_name] += 1

            return summary

        except Exception as e:
            logger.error(f"Error analyzing issues: {e}")
            return {}

    def _generate_recommendations(
        self,
        issues: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Generate browser recommendations.

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
            issue: Browser issue

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
