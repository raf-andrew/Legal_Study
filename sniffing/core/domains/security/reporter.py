"""
Security reporter for vulnerability and compliance reporting.
"""
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from ...base.reporter import BaseReporter
from ...utils.config import SnifferConfig
from ...utils.logging import setup_logger

logger = logging.getLogger("security_reporter")

class SecurityReporter(BaseReporter):
    """Reporter for security testing."""

    def __init__(self, config: SnifferConfig):
        """Initialize security reporter.

        Args:
            config: Reporter configuration
        """
        super().__init__("security", config)
        self.report_templates = self._load_report_templates()

    def _load_report_templates(self) -> Dict[str, Any]:
        """Load report templates.

        Returns:
            Dictionary of report templates
        """
        try:
            templates = self.config.get_reporter_config("security").get(
                "report_templates",
                {}
            )
            if not templates:
                logger.warning("No report templates configured")
            return templates

        except Exception as e:
            logger.error(f"Error loading report templates: {e}")
            return {}

    async def _generate_report(
        self,
        results: Dict[str, Any],
        analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate security report.

        Args:
            results: Sniffing results
            analysis: Analysis results

        Returns:
            Generated report
        """
        try:
            report = {
                "status": "running",
                "timestamp": datetime.now(),
                "results": results,
                "analysis": analysis,
                "sections": []
            }

            # Generate executive summary
            summary = await self._generate_executive_summary(
                results,
                analysis
            )
            report["sections"].append(summary)

            # Generate vulnerability section
            vulnerabilities = await self._generate_vulnerability_section(
                results.get("vulnerabilities", {}),
                analysis.get("vulnerability_findings", {})
            )
            report["sections"].append(vulnerabilities)

            # Generate compliance section
            compliance = await self._generate_compliance_section(
                results.get("compliance", {}),
                analysis.get("compliance_findings", {})
            )
            report["sections"].append(compliance)

            # Generate attack section
            attacks = await self._generate_attack_section(
                results.get("simulations", {}),
                analysis.get("attack_findings", {})
            )
            report["sections"].append(attacks)

            # Generate risk assessment
            risk = await self._generate_risk_assessment(
                analysis.get("risk_score", {})
            )
            report["sections"].append(risk)

            # Generate recommendations
            recommendations = await self._generate_recommendations(
                analysis.get("findings", [])
            )
            report["sections"].append(recommendations)

            # Update status
            report["status"] = "completed"

            return report

        except Exception as e:
            logger.error(f"Error generating security report: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now()
            }

    async def _generate_executive_summary(
        self,
        results: Dict[str, Any],
        analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate executive summary section.

        Args:
            results: Sniffing results
            analysis: Analysis results

        Returns:
            Summary section
        """
        try:
            # Get metrics
            findings = analysis.get("findings", [])
            risk_score = analysis.get("risk_score", {})
            coverage = results.get("coverage", {})

            # Create summary
            return {
                "name": "Executive Summary",
                "type": "summary",
                "content": {
                    "total_findings": len(findings),
                    "risk_score": risk_score.get("risk_score", 0.0),
                    "severity_distribution": risk_score.get("severity_counts", {}),
                    "type_distribution": risk_score.get("type_counts", {}),
                    "coverage": coverage.get("coverage_percent", 0.0),
                    "confidence": risk_score.get("confidence_avg", 0.0)
                },
                "quality": 1.0
            }

        except Exception as e:
            logger.error(f"Error generating executive summary: {e}")
            return {
                "name": "Executive Summary",
                "type": "summary",
                "error": str(e)
            }

    async def _generate_vulnerability_section(
        self,
        results: Dict[str, Any],
        analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate vulnerability section.

        Args:
            results: Vulnerability results
            analysis: Vulnerability analysis

        Returns:
            Vulnerability section
        """
        try:
            # Get findings
            findings = analysis.get("findings", [])

            # Create section
            return {
                "name": "Vulnerabilities",
                "type": "vulnerabilities",
                "content": {
                    "total": len(findings),
                    "findings": [
                        {
                            "id": finding.get("id"),
                            "pattern": finding.get("pattern"),
                            "severity": finding.get("severity"),
                            "confidence": finding.get("confidence"),
                            "description": finding.get("description"),
                            "code": finding.get("code"),
                            "line": finding.get("line"),
                            "cwe": finding.get("cwe"),
                            "cvss": finding.get("cvss"),
                            "references": finding.get("references"),
                            "remediation": finding.get("remediation")
                        }
                        for finding in findings
                    ]
                },
                "quality": sum(
                    finding.get("confidence", 0.0)
                    for finding in findings
                ) / len(findings) if findings else 0.0
            }

        except Exception as e:
            logger.error(f"Error generating vulnerability section: {e}")
            return {
                "name": "Vulnerabilities",
                "type": "vulnerabilities",
                "error": str(e)
            }

    async def _generate_compliance_section(
        self,
        results: Dict[str, Any],
        analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate compliance section.

        Args:
            results: Compliance results
            analysis: Compliance analysis

        Returns:
            Compliance section
        """
        try:
            # Get findings
            findings = analysis.get("findings", [])

            # Create section
            return {
                "name": "Compliance",
                "type": "compliance",
                "content": {
                    "total": len(findings),
                    "findings": [
                        {
                            "id": finding.get("id"),
                            "rule": finding.get("rule"),
                            "severity": finding.get("severity"),
                            "confidence": finding.get("confidence"),
                            "description": finding.get("description"),
                            "code": finding.get("code"),
                            "line": finding.get("line"),
                            "standard": finding.get("standard"),
                            "requirement": finding.get("requirement"),
                            "references": finding.get("references"),
                            "remediation": finding.get("remediation")
                        }
                        for finding in findings
                    ]
                },
                "quality": sum(
                    finding.get("confidence", 0.0)
                    for finding in findings
                ) / len(findings) if findings else 0.0
            }

        except Exception as e:
            logger.error(f"Error generating compliance section: {e}")
            return {
                "name": "Compliance",
                "type": "compliance",
                "error": str(e)
            }

    async def _generate_attack_section(
        self,
        results: Dict[str, Any],
        analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate attack section.

        Args:
            results: Attack results
            analysis: Attack analysis

        Returns:
            Attack section
        """
        try:
            # Get findings
            findings = analysis.get("findings", [])

            # Create section
            return {
                "name": "Attack Simulations",
                "type": "attacks",
                "content": {
                    "total": len(findings),
                    "findings": [
                        {
                            "id": finding.get("id"),
                            "pattern": finding.get("pattern"),
                            "severity": finding.get("severity"),
                            "confidence": finding.get("confidence"),
                            "description": finding.get("description"),
                            "code": finding.get("code"),
                            "line": finding.get("line"),
                            "technique": finding.get("technique"),
                            "mitre": finding.get("mitre"),
                            "references": finding.get("references"),
                            "remediation": finding.get("remediation")
                        }
                        for finding in findings
                    ]
                },
                "quality": sum(
                    finding.get("confidence", 0.0)
                    for finding in findings
                ) / len(findings) if findings else 0.0
            }

        except Exception as e:
            logger.error(f"Error generating attack section: {e}")
            return {
                "name": "Attack Simulations",
                "type": "attacks",
                "error": str(e)
            }

    async def _generate_risk_assessment(
        self,
        risk_score: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate risk assessment section.

        Args:
            risk_score: Risk score metrics

        Returns:
            Risk assessment section
        """
        try:
            return {
                "name": "Risk Assessment",
                "type": "risk",
                "content": {
                    "risk_score": risk_score.get("risk_score", 0.0),
                    "severity_distribution": risk_score.get("severity_counts", {}),
                    "type_distribution": risk_score.get("type_counts", {}),
                    "confidence": risk_score.get("confidence_avg", 0.0),
                    "assessment": self._get_risk_assessment(
                        risk_score.get("risk_score", 0.0)
                    )
                },
                "quality": 1.0
            }

        except Exception as e:
            logger.error(f"Error generating risk assessment: {e}")
            return {
                "name": "Risk Assessment",
                "type": "risk",
                "error": str(e)
            }

    def _get_risk_assessment(self, risk_score: float) -> str:
        """Get risk assessment text.

        Args:
            risk_score: Risk score value

        Returns:
            Risk assessment text
        """
        if risk_score >= 50.0:
            return "Critical risk level - Immediate action required"
        elif risk_score >= 25.0:
            return "High risk level - Urgent action required"
        elif risk_score >= 10.0:
            return "Medium risk level - Action required"
        elif risk_score > 0.0:
            return "Low risk level - Action recommended"
        else:
            return "No risk detected"

    async def _generate_recommendations(
        self,
        findings: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate recommendations section.

        Args:
            findings: Analysis findings

        Returns:
            Recommendations section
        """
        try:
            # Group findings by severity
            grouped = {}
            for finding in findings:
                severity = finding.get("severity", "medium")
                if severity not in grouped:
                    grouped[severity] = []
                grouped[severity].append(finding)

            # Generate recommendations
            recommendations = []
            for severity in ["critical", "high", "medium", "low"]:
                if severity in grouped:
                    recommendations.extend([
                        {
                            "id": finding.get("id"),
                            "type": finding.get("type"),
                            "severity": severity,
                            "description": finding.get("description"),
                            "remediation": finding.get("remediation")
                        }
                        for finding in grouped[severity]
                    ])

            return {
                "name": "Recommendations",
                "type": "recommendations",
                "content": {
                    "total": len(recommendations),
                    "recommendations": recommendations
                },
                "quality": 1.0
            }

        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return {
                "name": "Recommendations",
                "type": "recommendations",
                "error": str(e)
            }
