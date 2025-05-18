"""
Base sniffer class for domain-specific sniffing.
"""
import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from ..utils.logging import setup_logger
from ..utils.metrics import MetricsCollector

logger = logging.getLogger(__name__)

class BaseSniffer(ABC):
    """Base class for all sniffers."""

    def __init__(self, config: Dict, domain: str):
        """Initialize base sniffer.

        Args:
            config: Sniffer configuration
            domain: Sniffer domain
        """
        self.config = config
        self.domain = domain

        # Set up logging
        setup_logger(
            logger,
            config["monitoring"]["logging"],
            f"{domain}_sniffer"
        )

        # Initialize metrics
        self.metrics = MetricsCollector(f"{domain}_sniffer")

        # Initialize state
        self.results = {}
        self.active_jobs = set()
        self.is_running = False

    async def start(self) -> None:
        """Start sniffer."""
        try:
            logger.info(f"Starting {self.domain} sniffer")
            self.is_running = True

        except Exception as e:
            logger.error(f"Error starting {self.domain} sniffer: {e}")
            self.is_running = False
            raise

    async def stop(self) -> None:
        """Stop sniffer."""
        try:
            logger.info(f"Stopping {self.domain} sniffer")
            self.is_running = False

            # Wait for jobs to complete
            while self.active_jobs:
                await asyncio.sleep(0.1)

            logger.info(f"{self.domain} sniffer stopped")

        except Exception as e:
            logger.error(f"Error stopping {self.domain} sniffer: {e}")
            raise

    @abstractmethod
    async def sniff_file(self, file: str) -> Dict:
        """Sniff a single file.

        Args:
            file: File to sniff

        Returns:
            Sniffing results
        """
        pass

    async def analyze_result(
        self,
        file: str,
        result: Dict
    ) -> Dict:
        """Analyze sniffing result.

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
        issues: List[Dict]
    ) -> Dict:
        """Fix detected issues.

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

    def _analyze_issues(self, issues: List[Dict]) -> Dict:
        """Analyze issues.

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
                "types": {}
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
                issue_type = issue.get("type", "other")
                if issue_type not in summary["types"]:
                    summary["types"][issue_type] = 0
                summary["types"][issue_type] += 1

            return summary

        except Exception as e:
            logger.error(f"Error analyzing issues: {e}")
            return {}

    def _generate_recommendations(self, issues: List[Dict]) -> List[Dict]:
        """Generate recommendations.

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

    def _get_fix(self, issue: Dict) -> Optional[Dict]:
        """Get fix for issue.

        Args:
            issue: Issue to fix

        Returns:
            Fix configuration or None
        """
        try:
            # Get fix from issue
            return issue.get("fix")

        except Exception as e:
            logger.error(f"Error getting fix: {e}")
            return None

    def _apply_fix(self, content: str, fix: Dict) -> str:
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

    def _apply_replace_fix(self, content: str, fix: Dict) -> str:
        """Apply replace fix.

        Args:
            content: File content
            fix: Fix configuration

        Returns:
            Modified content
        """
        try:
            import re
            pattern = fix.get("pattern")
            replacement = fix.get("replacement")
            if not pattern or not replacement:
                return content

            return re.sub(pattern, replacement, content)

        except Exception as e:
            logger.error(f"Error applying replace fix: {e}")
            return content

    def _apply_insert_fix(self, content: str, fix: Dict) -> str:
        """Apply insert fix.

        Args:
            content: File content
            fix: Fix configuration

        Returns:
            Modified content
        """
        try:
            position = fix.get("position", "after")
            target = fix.get("target")
            insert = fix.get("content")
            if not target or not insert:
                return content

            import re
            match = re.search(target, content)
            if not match:
                return content

            if position == "before":
                return (
                    content[:match.start()] +
                    insert +
                    content[match.start():]
                )
            else:
                return (
                    content[:match.end()] +
                    insert +
                    content[match.end():]
                )

        except Exception as e:
            logger.error(f"Error applying insert fix: {e}")
            return content

    def _apply_delete_fix(self, content: str, fix: Dict) -> str:
        """Apply delete fix.

        Args:
            content: File content
            fix: Fix configuration

        Returns:
            Modified content
        """
        try:
            pattern = fix.get("pattern")
            if not pattern:
                return content

            import re
            return re.sub(pattern, "", content)

        except Exception as e:
            logger.error(f"Error applying delete fix: {e}")
            return content

    def _get_recommendation(self, issue: Dict) -> Optional[Dict]:
        """Get recommendation for issue.

        Args:
            issue: Issue to fix

        Returns:
            Recommendation or None
        """
        try:
            # Get recommendation from issue
            return issue.get("recommendation")

        except Exception as e:
            logger.error(f"Error getting recommendation: {e}")
            return None

    def get_metrics(self) -> Dict:
        """Get sniffer metrics.

        Returns:
            Metrics dictionary
        """
        try:
            metrics = {
                "active_jobs": len(self.active_jobs),
                "stored_results": len(self.results),
                "domain": self.domain,
                "status": "running" if self.is_running else "stopped"
            }

            # Calculate success rate
            total = len(self.results)
            if total > 0:
                success = sum(
                    1 for r in self.results.values()
                    if r.get("status") == "success"
                )
                metrics["success_rate"] = success / total

            # Add collector metrics
            metrics.update(self.metrics.get_metrics())

            return metrics

        except Exception as e:
            logger.error(f"Error getting metrics: {e}")
            return {}
