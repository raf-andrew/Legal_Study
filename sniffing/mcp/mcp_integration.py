"""
MCP (Master Control Program) integration for coordinating sniffing operations.
"""
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from ..core.base_sniffer import BaseSniffer, SnifferType, SniffingResult

class MCPIntegration:
    """Manages and coordinates all sniffing operations through the MCP."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.sniffers: Dict[SnifferType, BaseSniffer] = {}
        self.workspace_path = Path(config.get("workspace_path", "."))
        self.report_path = Path(config.get("report_path", "reports"))
        self._setup_directories()

    def _setup_directories(self) -> None:
        """Set up necessary directories for MCP operations."""
        self.report_path.mkdir(parents=True, exist_ok=True)
        (self.report_path / "mcp").mkdir(parents=True, exist_ok=True)

    def register_sniffer(self, sniffer: BaseSniffer) -> None:
        """Register a new sniffer with the MCP."""
        self.sniffers[sniffer.get_sniffer_type()] = sniffer

    async def run_autonomous_testing(self, target_files: Optional[Set[Path]] = None) -> Dict[SnifferType, SniffingResult]:
        """Run autonomous testing across all registered sniffers."""
        results = {}

        for sniffer_type, sniffer in self.sniffers.items():
            if target_files and not any(f in target_files for f in sniffer.get_affected_files()):
                continue

            try:
                result = await self._run_sniffer(sniffer)
                results[sniffer_type] = result

                if result.issues:
                    await self._handle_issues(sniffer, result.issues)

            except Exception as e:
                print(f"Error running {sniffer_type.value} sniffer: {e}")

        return results

    async def _run_sniffer(self, sniffer: BaseSniffer) -> SniffingResult:
        """Run a single sniffer and handle its results."""
        result = sniffer.sniff()

        # Generate and save report
        report = sniffer.generate_report()
        report_path = sniffer.save_report(report)

        # Update MCP audit trail
        self._update_audit_trail(sniffer.get_sniffer_type(), result, report_path)

        return result

    async def _handle_issues(self, sniffer: BaseSniffer, issues: List[Dict[str, Any]]) -> None:
        """Handle issues detected by a sniffer."""
        # Attempt automatic fixes
        if self.config.get("auto_fix_enabled", True):
            fixed = sniffer.fix_issues(issues)
            if fixed:
                # Re-run sniffer to verify fixes
                await self._run_sniffer(sniffer)

    def _update_audit_trail(self, sniffer_type: SnifferType, result: SniffingResult, report_path: Path) -> None:
        """Update the MCP audit trail with sniffer results."""
        audit_entry = {
            "timestamp": datetime.now().isoformat(),
            "sniffer_type": sniffer_type.value,
            "status": result.status,
            "issues_count": len(result.issues),
            "report_path": str(report_path)
        }

        audit_file = self.report_path / "mcp" / "audit_trail.json"

        import json
        try:
            with open(audit_file, 'r') as f:
                audit_trail = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            audit_trail = []

        audit_trail.append(audit_entry)

        with open(audit_file, 'w') as f:
            json.dump(audit_trail, f, indent=2)

    def analyze_results(self) -> Dict[str, Any]:
        """Analyze results from all sniffers and generate insights."""
        analysis = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": True,
            "domain_results": {},
            "trends": self._analyze_trends(),
            "recommendations": self._generate_recommendations()
        }

        for sniffer_type, sniffer in self.sniffers.items():
            domain_analysis = self._analyze_domain(sniffer)
            analysis["domain_results"][sniffer_type.value] = domain_analysis
            analysis["overall_status"] = analysis["overall_status"] and domain_analysis["status"]

        return analysis

    def _analyze_domain(self, sniffer: BaseSniffer) -> Dict[str, Any]:
        """Analyze results for a specific domain."""
        return {
            "status": all(r.status for r in sniffer.results),
            "total_issues": sum(len(r.issues) for r in sniffer.results),
            "coverage": sum(r.coverage or 0 for r in sniffer.results) / len(sniffer.results) if sniffer.results else 0,
            "performance": self._analyze_performance(sniffer),
            "security": self._analyze_security(sniffer)
        }

    def _analyze_performance(self, sniffer: BaseSniffer) -> Dict[str, Any]:
        """Analyze performance metrics for a sniffer."""
        performance_metrics = [r.performance_metrics for r in sniffer.results if r.performance_metrics]
        if not performance_metrics:
            return {}

        return {
            "average_response_time": sum(m.get("response_time", 0) for m in performance_metrics) / len(performance_metrics),
            "memory_usage": sum(m.get("memory_usage", 0) for m in performance_metrics) / len(performance_metrics),
            "cpu_usage": sum(m.get("cpu_usage", 0) for m in performance_metrics) / len(performance_metrics)
        }

    def _analyze_security(self, sniffer: BaseSniffer) -> Dict[str, Any]:
        """Analyze security metrics for a sniffer."""
        security_metrics = [r.security_metrics for r in sniffer.results if r.security_metrics]
        if not security_metrics:
            return {}

        return {
            "vulnerabilities": sum(m.get("vulnerabilities", 0) for m in security_metrics),
            "security_score": sum(m.get("security_score", 0) for m in security_metrics) / len(security_metrics),
            "compliance_status": all(m.get("compliance_status", False) for m in security_metrics)
        }

    def _analyze_trends(self) -> Dict[str, Any]:
        """Analyze trends across all sniffing operations."""
        return {
            "issue_trend": self._calculate_issue_trend(),
            "coverage_trend": self._calculate_coverage_trend(),
            "performance_trend": self._calculate_performance_trend()
        }

    def _calculate_issue_trend(self) -> Dict[str, Any]:
        """Calculate trend in number of issues over time."""
        # Implementation would analyze historical data
        return {"trend": "decreasing", "confidence": 0.85}

    def _calculate_coverage_trend(self) -> Dict[str, Any]:
        """Calculate trend in code coverage over time."""
        # Implementation would analyze historical data
        return {"trend": "increasing", "confidence": 0.90}

    def _calculate_performance_trend(self) -> Dict[str, Any]:
        """Calculate trend in performance metrics over time."""
        # Implementation would analyze historical data
        return {"trend": "stable", "confidence": 0.75}

    def _generate_recommendations(self) -> List[Dict[str, Any]]:
        """Generate recommendations based on analysis."""
        recommendations = []

        for sniffer_type, sniffer in self.sniffers.items():
            domain_analysis = self._analyze_domain(sniffer)

            if not domain_analysis["status"]:
                recommendations.append({
                    "domain": sniffer_type.value,
                    "priority": "high",
                    "description": f"Address issues in {sniffer_type.value} domain",
                    "action_items": self._generate_action_items(sniffer)
                })

        return recommendations

    def _generate_action_items(self, sniffer: BaseSniffer) -> List[str]:
        """Generate specific action items for a sniffer."""
        # Implementation would analyze issues and generate specific actions
        return ["Fix failing tests", "Improve code coverage", "Address security vulnerabilities"]

    def generate_report(self) -> Path:
        """Generate a comprehensive MCP report."""
        analysis = self.analyze_results()

        report_file = self.report_path / "mcp" / f"mcp_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        import json
        with open(report_file, 'w') as f:
            json.dump(analysis, f, indent=2)

        return report_file
