"""
Security analyzer for vulnerability and compliance analysis.
"""
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from ...base.analyzer import BaseAnalyzer
from ...utils.config import SnifferConfig
from ...utils.logging import setup_logger

logger = logging.getLogger("security_analyzer")

class SecurityAnalyzer(BaseAnalyzer):
    """Analyzer for security testing."""

    def __init__(self, config: SnifferConfig):
        """Initialize security analyzer.

        Args:
            config: Analyzer configuration
        """
        super().__init__("security", config)
        self.vulnerability_patterns = self._load_vulnerability_patterns()
        self.compliance_rules = self._load_compliance_rules()
        self.attack_patterns = self._load_attack_patterns()

    def _load_vulnerability_patterns(self) -> Dict[str, Any]:
        """Load vulnerability patterns.

        Returns:
            Dictionary of vulnerability patterns
        """
        try:
            patterns = self.config.get_analyzer_config("security").get(
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
            rules = self.config.get_analyzer_config("security").get(
                "compliance_rules",
                {}
            )
            if not rules:
                logger.warning("No compliance rules configured")
            return rules

        except Exception as e:
            logger.error(f"Error loading compliance rules: {e}")
            return {}

    def _load_attack_patterns(self) -> Dict[str, Any]:
        """Load attack patterns.

        Returns:
            Dictionary of attack patterns
        """
        try:
            patterns = self.config.get_analyzer_config("security").get(
                "attack_patterns",
                {}
            )
            if not patterns:
                logger.warning("No attack patterns configured")
            return patterns

        except Exception as e:
            logger.error(f"Error loading attack patterns: {e}")
            return {}

    async def _analyze_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze security results.

        Args:
            results: Results to analyze

        Returns:
            Analysis results
        """
        try:
            analysis = {
                "status": "running",
                "timestamp": datetime.now(),
                "results": results,
                "findings": []
            }

            # Analyze vulnerabilities
            vulnerability_findings = await self._analyze_vulnerabilities(
                results.get("vulnerabilities", {})
            )
            analysis["vulnerability_findings"] = vulnerability_findings

            # Analyze compliance
            compliance_findings = await self._analyze_compliance(
                results.get("compliance", {})
            )
            analysis["compliance_findings"] = compliance_findings

            # Analyze attacks
            attack_findings = await self._analyze_attacks(
                results.get("simulations", {})
            )
            analysis["attack_findings"] = attack_findings

            # Aggregate findings
            findings = []
            findings.extend(vulnerability_findings.get("findings", []))
            findings.extend(compliance_findings.get("findings", []))
            findings.extend(attack_findings.get("findings", []))
            analysis["findings"] = findings

            # Calculate risk score
            risk_score = await self._calculate_risk_score(findings)
            analysis["risk_score"] = risk_score

            # Update status
            analysis["status"] = "completed"

            return analysis

        except Exception as e:
            logger.error(f"Error analyzing security results: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now()
            }

    async def _analyze_vulnerabilities(
        self,
        results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze vulnerability results.

        Args:
            results: Results to analyze

        Returns:
            Analysis findings
        """
        try:
            findings = {
                "status": "running",
                "timestamp": datetime.now(),
                "findings": []
            }

            # Process each issue
            for issue in results.get("issues", []):
                # Get pattern
                pattern_id = issue.get("pattern")
                pattern = self.vulnerability_patterns.get(pattern_id)
                if not pattern:
                    continue

                # Analyze issue
                finding = await self._analyze_vulnerability(issue, pattern)
                if finding:
                    findings["findings"].append(finding)

            # Update status
            findings["status"] = "completed"

            return findings

        except Exception as e:
            logger.error(f"Error analyzing vulnerabilities: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now()
            }

    async def _analyze_vulnerability(
        self,
        issue: Dict[str, Any],
        pattern: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Analyze vulnerability issue.

        Args:
            issue: Issue to analyze
            pattern: Pattern used to detect issue

        Returns:
            Analysis finding or None
        """
        try:
            # Get code snippet
            code = issue.get("code", "")
            if not code:
                return None

            # Encode code
            inputs = self.tokenizer(
                code,
                return_tensors="pt",
                padding=True,
                truncation=True
            )

            # Get embeddings
            outputs = self.model(**inputs)
            embeddings = outputs.last_hidden_state.mean(dim=1)

            # Calculate confidence
            confidence = float(embeddings.max().item())

            # Create finding
            return {
                "id": issue.get("id"),
                "type": "vulnerability",
                "pattern": pattern.get("name"),
                "severity": pattern.get("severity", "medium"),
                "confidence": confidence,
                "description": pattern.get("description"),
                "code": code,
                "line": issue.get("line"),
                "cwe": pattern.get("cwe"),
                "cvss": pattern.get("cvss"),
                "references": pattern.get("references"),
                "remediation": pattern.get("remediation")
            }

        except Exception as e:
            logger.error(f"Error analyzing vulnerability: {e}")
            return None

    async def _analyze_compliance(
        self,
        results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze compliance results.

        Args:
            results: Results to analyze

        Returns:
            Analysis findings
        """
        try:
            findings = {
                "status": "running",
                "timestamp": datetime.now(),
                "findings": []
            }

            # Process each issue
            for issue in results.get("issues", []):
                # Get rule
                rule_id = issue.get("rule")
                rule = self.compliance_rules.get(rule_id)
                if not rule:
                    continue

                # Analyze issue
                finding = await self._analyze_compliance_issue(issue, rule)
                if finding:
                    findings["findings"].append(finding)

            # Update status
            findings["status"] = "completed"

            return findings

        except Exception as e:
            logger.error(f"Error analyzing compliance: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now()
            }

    async def _analyze_compliance_issue(
        self,
        issue: Dict[str, Any],
        rule: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Analyze compliance issue.

        Args:
            issue: Issue to analyze
            rule: Rule used to detect issue

        Returns:
            Analysis finding or None
        """
        try:
            # Get code snippet
            code = issue.get("code", "")
            if not code:
                return None

            # Encode code
            inputs = self.tokenizer(
                code,
                return_tensors="pt",
                padding=True,
                truncation=True
            )

            # Get embeddings
            outputs = self.model(**inputs)
            embeddings = outputs.last_hidden_state.mean(dim=1)

            # Calculate confidence
            confidence = float(embeddings.max().item())

            # Create finding
            return {
                "id": issue.get("id"),
                "type": "compliance",
                "rule": rule.get("name"),
                "severity": rule.get("severity", "medium"),
                "confidence": confidence,
                "description": rule.get("description"),
                "code": code,
                "line": issue.get("line"),
                "standard": rule.get("standard"),
                "requirement": rule.get("requirement"),
                "references": rule.get("references"),
                "remediation": rule.get("remediation")
            }

        except Exception as e:
            logger.error(f"Error analyzing compliance issue: {e}")
            return None

    async def _analyze_attacks(
        self,
        results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze attack simulation results.

        Args:
            results: Results to analyze

        Returns:
            Analysis findings
        """
        try:
            findings = {
                "status": "running",
                "timestamp": datetime.now(),
                "findings": []
            }

            # Process each issue
            for issue in results.get("issues", []):
                # Get pattern
                pattern_id = issue.get("simulation")
                pattern = self.attack_patterns.get(pattern_id)
                if not pattern:
                    continue

                # Analyze issue
                finding = await self._analyze_attack(issue, pattern)
                if finding:
                    findings["findings"].append(finding)

            # Update status
            findings["status"] = "completed"

            return findings

        except Exception as e:
            logger.error(f"Error analyzing attacks: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now()
            }

    async def _analyze_attack(
        self,
        issue: Dict[str, Any],
        pattern: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Analyze attack simulation issue.

        Args:
            issue: Issue to analyze
            pattern: Pattern used to detect issue

        Returns:
            Analysis finding or None
        """
        try:
            # Get code snippet
            code = issue.get("code", "")
            if not code:
                return None

            # Encode code
            inputs = self.tokenizer(
                code,
                return_tensors="pt",
                padding=True,
                truncation=True
            )

            # Get embeddings
            outputs = self.model(**inputs)
            embeddings = outputs.last_hidden_state.mean(dim=1)

            # Calculate confidence
            confidence = float(embeddings.max().item())

            # Create finding
            return {
                "id": issue.get("id"),
                "type": "attack",
                "pattern": pattern.get("name"),
                "severity": pattern.get("severity", "medium"),
                "confidence": confidence,
                "description": pattern.get("description"),
                "code": code,
                "line": issue.get("line"),
                "technique": pattern.get("technique"),
                "mitre": pattern.get("mitre"),
                "references": pattern.get("references"),
                "remediation": pattern.get("remediation")
            }

        except Exception as e:
            logger.error(f"Error analyzing attack: {e}")
            return None

    async def _calculate_risk_score(
        self,
        findings: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate risk score from findings.

        Args:
            findings: Findings to calculate score from

        Returns:
            Risk score metrics
        """
        try:
            # Initialize metrics
            metrics = {
                "total_findings": len(findings),
                "severity_counts": {
                    "critical": 0,
                    "high": 0,
                    "medium": 0,
                    "low": 0
                },
                "type_counts": {
                    "vulnerability": 0,
                    "compliance": 0,
                    "attack": 0
                },
                "confidence_avg": 0.0
            }

            # Calculate metrics
            confidence_sum = 0.0
            for finding in findings:
                # Count severity
                severity = finding.get("severity", "medium").lower()
                metrics["severity_counts"][severity] += 1

                # Count type
                finding_type = finding.get("type", "unknown")
                if finding_type in metrics["type_counts"]:
                    metrics["type_counts"][finding_type] += 1

                # Sum confidence
                confidence_sum += finding.get("confidence", 0.0)

            # Calculate confidence average
            if findings:
                metrics["confidence_avg"] = confidence_sum / len(findings)

            # Calculate risk score
            risk_score = (
                metrics["severity_counts"]["critical"] * 10.0 +
                metrics["severity_counts"]["high"] * 5.0 +
                metrics["severity_counts"]["medium"] * 2.0 +
                metrics["severity_counts"]["low"] * 1.0
            ) * metrics["confidence_avg"]

            metrics["risk_score"] = risk_score

            return metrics

        except Exception as e:
            logger.error(f"Error calculating risk score: {e}")
            return {
                "total_findings": 0,
                "severity_counts": {
                    "critical": 0,
                    "high": 0,
                    "medium": 0,
                    "low": 0
                },
                "type_counts": {
                    "vulnerability": 0,
                    "compliance": 0,
                    "attack": 0
                },
                "confidence_avg": 0.0,
                "risk_score": 0.0
            }
