"""
Functional domain sniffer for API, integration, and workflow testing.
"""
import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import yaml

from ...base import BaseSniffer
from ...utils.logging import setup_logger
from ...utils.metrics import MetricsCollector, track_operation

logger = logging.getLogger(__name__)

class FunctionalSniffer(BaseSniffer):
    """Functional domain sniffer implementation."""

    def __init__(self, config: Dict):
        """Initialize functional sniffer.

        Args:
            config: Sniffer configuration
        """
        super().__init__(config, "functional")

        # Set up logging
        setup_logger(
            logger,
            config["monitoring"]["logging"],
            "functional_sniffer"
        )

        # Initialize metrics
        self.metrics = MetricsCollector("functional_sniffer")

        # Load patterns and rules
        self.patterns = self._load_patterns()
        self.rules = self._load_rules()
        self.simulations = self._load_simulations()

    def _load_patterns(self) -> Dict:
        """Load functional patterns.

        Returns:
            Pattern dictionary
        """
        try:
            patterns_path = Path(self.config["domains"]["functional"]["patterns_path"])
            if not patterns_path.exists():
                return {}

            # Load patterns
            patterns = {}
            for pattern_file in patterns_path.glob("*.yaml"):
                with open(pattern_file) as f:
                    patterns.update(yaml.safe_load(f))

            logger.info(f"Loaded {len(patterns)} functional patterns")
            return patterns

        except Exception as e:
            logger.error(f"Error loading functional patterns: {e}")
            return {}

    def _load_rules(self) -> Dict:
        """Load functional rules.

        Returns:
            Rules dictionary
        """
        try:
            rules_path = Path(self.config["domains"]["functional"]["rules_path"])
            if not rules_path.exists():
                return {}

            # Load rules
            rules = {}
            for rule_file in rules_path.glob("*.yaml"):
                with open(rule_file) as f:
                    rules.update(yaml.safe_load(f))

            logger.info(f"Loaded {len(rules)} functional rules")
            return rules

        except Exception as e:
            logger.error(f"Error loading functional rules: {e}")
            return {}

    def _load_simulations(self) -> Dict:
        """Load functional simulations.

        Returns:
            Simulations dictionary
        """
        try:
            sims_path = Path(self.config["domains"]["functional"]["simulations_path"])
            if not sims_path.exists():
                return {}

            # Load simulations
            simulations = {}
            for sim_file in sims_path.glob("*.yaml"):
                with open(sim_file) as f:
                    simulations.update(yaml.safe_load(f))

            logger.info(f"Loaded {len(simulations)} functional simulations")
            return simulations

        except Exception as e:
            logger.error(f"Error loading functional simulations: {e}")
            return {}

    @track_operation("functional_sniff")
    async def sniff_file(self, file: str) -> Dict:
        """Sniff file for functional issues.

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
            sim_issues = await self._run_simulations(file)
            results["issues"].extend(sim_issues)

            # Calculate metrics
            results["metrics"] = self._calculate_metrics(results["issues"])

            # Update status
            results["status"] = "completed"
            if any(issue["severity"] in ["critical", "high"]
                  for issue in results["issues"]):
                results["status"] = "failed"

            return results

        except Exception as e:
            logger.error(f"Error sniffing file {file}: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    async def _check_patterns(self, content: str) -> List[Dict]:
        """Check content against functional patterns.

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
                            "match": match.group(0),
                            "fix": pattern.get("fix"),
                            "recommendation": pattern.get("recommendation")
                        })

                except Exception as e:
                    logger.error(f"Error checking pattern {pattern_name}: {e}")

            return issues

        except Exception as e:
            logger.error(f"Error checking patterns: {e}")
            return []

    async def _check_rules(self, content: str) -> List[Dict]:
        """Check content against functional rules.

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

    async def _run_simulations(self, file: str) -> List[Dict]:
        """Run functional simulations.

        Args:
            file: File to simulate

        Returns:
            List of simulation issues
        """
        try:
            issues = []

            # Run each simulation
            for sim_name, simulation in self.simulations.items():
                try:
                    # Get simulator
                    simulator = self._get_simulator(simulation)
                    if not simulator:
                        continue

                    # Run simulation
                    sim_issues = await simulator(file, simulation)
                    for issue in sim_issues:
                        issue.update({
                            "type": "simulation",
                            "name": sim_name
                        })
                        issues.append(issue)

                except Exception as e:
                    logger.error(f"Error running simulation {sim_name}: {e}")

            return issues

        except Exception as e:
            logger.error(f"Error running simulations: {e}")
            return []

    def _get_rule_checker(self, category: Dict):
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
            if category_type == "api":
                return self._check_api_rules
            elif category_type == "integration":
                return self._check_integration_rules
            elif category_type == "workflow":
                return self._check_workflow_rules

            return None

        except Exception as e:
            logger.error(f"Error getting rule checker: {e}")
            return None

    def _get_simulator(self, simulation: Dict):
        """Get simulation function.

        Args:
            simulation: Simulation configuration

        Returns:
            Simulation function or None
        """
        try:
            sim_type = simulation.get("type")
            if not sim_type:
                return None

            # Get simulator
            if sim_type == "api":
                return self._simulate_api
            elif sim_type == "integration":
                return self._simulate_integration
            elif sim_type == "workflow":
                return self._simulate_workflow

            return None

        except Exception as e:
            logger.error(f"Error getting simulator: {e}")
            return None

    async def _check_api_rules(
        self,
        content: str,
        category: Dict
    ) -> List[Dict]:
        """Check API rules.

        Args:
            content: File content
            category: Rule category

        Returns:
            List of rule issues
        """
        try:
            issues = []

            # Check each rule
            for rule_name, rule in category["rules"].items():
                try:
                    # Check rule pattern
                    import re
                    matches = re.finditer(rule["pattern"], content)
                    for match in matches:
                        # Get API metrics
                        metrics = self._analyze_api(
                            content[
                                max(0, match.start() - 50):
                                min(len(content), match.end() + 50)
                            ]
                        )

                        # Check thresholds
                        if metrics["score"] < rule.get("min_score", 0.8):
                            issues.append({
                                "name": rule_name,
                                "severity": rule.get("severity", "medium"),
                                "description": rule.get("description", ""),
                                "line": content.count("\n", 0, match.start()) + 1,
                                "match": match.group(0),
                                "metrics": metrics,
                                "fix": rule.get("fix"),
                                "recommendation": rule.get("recommendation")
                            })

                except Exception as e:
                    logger.error(f"Error checking rule {rule_name}: {e}")

            return issues

        except Exception as e:
            logger.error(f"Error checking API rules: {e}")
            return []

    def _analyze_api(self, code: str) -> Dict:
        """Analyze API code.

        Args:
            code: Code to analyze

        Returns:
            API metrics
        """
        try:
            # Simple heuristic analysis
            # TODO: Implement more sophisticated analysis
            metrics = {
                "endpoints": 0,
                "methods": 0,
                "params": 0,
                "validation": 0,
                "score": 1.0
            }

            # Check endpoints
            metrics["endpoints"] = code.count("@app.route") + code.count("@api")
            if metrics["endpoints"] == 0:
                metrics["score"] *= 0.8

            # Check methods
            metrics["methods"] = (
                code.count("GET") +
                code.count("POST") +
                code.count("PUT") +
                code.count("DELETE")
            )
            if metrics["methods"] == 0:
                metrics["score"] *= 0.8

            # Check parameters
            metrics["params"] = code.count("request.") + code.count("params")
            if metrics["params"] > 0 and code.count("validate") == 0:
                metrics["score"] *= 0.9

            # Check validation
            metrics["validation"] = (
                code.count("validate") +
                code.count("schema") +
                code.count("type:")
            )
            if metrics["validation"] == 0:
                metrics["score"] *= 0.9

            return metrics

        except Exception as e:
            logger.error(f"Error analyzing API: {e}")
            return {
                "endpoints": 0,
                "methods": 0,
                "params": 0,
                "validation": 0,
                "score": 0.0
            }

    def _calculate_metrics(self, issues: List[Dict]) -> Dict:
        """Calculate functional metrics.

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
