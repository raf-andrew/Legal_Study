"""
Documentation domain sniffer for documentation quality and completeness.
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

class DocumentationSniffer(BaseSniffer):
    """Documentation domain sniffer implementation."""

    def __init__(self, config: Dict):
        """Initialize documentation sniffer.

        Args:
            config: Sniffer configuration
        """
        super().__init__(config, "documentation")

        # Set up logging
        setup_logger(
            logger,
            config["monitoring"]["logging"],
            "documentation_sniffer"
        )

        # Initialize metrics
        self.metrics = MetricsCollector("documentation_sniffer")

        # Load patterns and rules
        self.patterns = self._load_patterns()
        self.rules = self._load_rules()

    def _load_patterns(self) -> Dict:
        """Load documentation patterns.

        Returns:
            Pattern dictionary
        """
        try:
            patterns_path = Path(self.config["domains"]["documentation"]["patterns_path"])
            if not patterns_path.exists():
                return {}

            # Load patterns
            patterns = {}
            for pattern_file in patterns_path.glob("*.yaml"):
                with open(pattern_file) as f:
                    patterns.update(yaml.safe_load(f))

            logger.info(f"Loaded {len(patterns)} documentation patterns")
            return patterns

        except Exception as e:
            logger.error(f"Error loading documentation patterns: {e}")
            return {}

    def _load_rules(self) -> Dict:
        """Load documentation rules.

        Returns:
            Rules dictionary
        """
        try:
            rules_path = Path(self.config["domains"]["documentation"]["rules_path"])
            if not rules_path.exists():
                return {}

            # Load rules
            rules = {}
            for rule_file in rules_path.glob("*.yaml"):
                with open(rule_file) as f:
                    rules.update(yaml.safe_load(f))

            logger.info(f"Loaded {len(rules)} documentation rules")
            return rules

        except Exception as e:
            logger.error(f"Error loading documentation rules: {e}")
            return {}

    @track_operation("documentation_sniff")
    async def sniff_file(self, file: str) -> Dict:
        """Sniff file for documentation issues.

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
        """Check content against documentation patterns.

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
        """Check content against documentation rules.

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
            if category_type == "completeness":
                return self._check_completeness_rules
            elif category_type == "quality":
                return self._check_quality_rules
            elif category_type == "style":
                return self._check_style_rules

            return None

        except Exception as e:
            logger.error(f"Error getting rule checker: {e}")
            return None

    async def _check_completeness_rules(
        self,
        content: str,
        category: Dict
    ) -> List[Dict]:
        """Check documentation completeness rules.

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
                    # Get completeness metrics
                    metrics = self._analyze_completeness(content)

                    # Check thresholds
                    if metrics["score"] < rule.get("min_score", 0.8):
                        issues.append({
                            "name": rule_name,
                            "severity": rule.get("severity", "medium"),
                            "description": rule.get("description", ""),
                            "metrics": metrics,
                            "fix": rule.get("fix"),
                            "recommendation": rule.get("recommendation")
                        })

                except Exception as e:
                    logger.error(f"Error checking rule {rule_name}: {e}")

            return issues

        except Exception as e:
            logger.error(f"Error checking completeness rules: {e}")
            return []

    def _analyze_completeness(self, code: str) -> Dict:
        """Analyze documentation completeness.

        Args:
            code: Code to analyze

        Returns:
            Completeness metrics
        """
        try:
            # Simple heuristic analysis
            # TODO: Implement more sophisticated analysis
            metrics = {
                "total_items": 0,
                "documented_items": 0,
                "completeness": 0.0,
                "score": 1.0
            }

            # Count items
            items = []

            # Find classes
            import re
            class_matches = re.finditer(r"class\s+(\w+)", code)
            for match in class_matches:
                items.append({
                    "type": "class",
                    "name": match.group(1),
                    "start": match.start()
                })

            # Find functions
            func_matches = re.finditer(r"def\s+(\w+)", code)
            for match in func_matches:
                items.append({
                    "type": "function",
                    "name": match.group(1),
                    "start": match.start()
                })

            # Count total items
            metrics["total_items"] = len(items)

            # Count documented items
            for item in items:
                # Get item context
                start = max(0, item["start"] - 200)
                end = min(len(code), item["start"] + 200)
                context = code[start:end]

                # Check for docstring
                if '"""' in context or "'''" in context:
                    metrics["documented_items"] += 1

            # Calculate completeness
            if metrics["total_items"] > 0:
                metrics["completeness"] = (
                    metrics["documented_items"] / metrics["total_items"]
                ) * 100
                metrics["score"] = metrics["completeness"] / 100

            return metrics

        except Exception as e:
            logger.error(f"Error analyzing completeness: {e}")
            return {
                "total_items": 0,
                "documented_items": 0,
                "completeness": 0.0,
                "score": 0.0
            }

    def _calculate_metrics(self, issues: List[Dict]) -> Dict:
        """Calculate documentation metrics.

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
                    "rule": 0
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
