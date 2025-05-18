#!/usr/bin/env python3
"""
Core Sniffing Module
This module implements the base sniffing functionality and coordination
"""

import os
import sys
import logging
import asyncio
import json
from pathlib import Path
from typing import Dict, List, Optional, Set, Any, Type
from datetime import datetime
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor

from ..config import SNIFFING_CONFIG

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/sniffing/core.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

@dataclass
class SniffResult:
    """Data class for sniffing results"""
    file_path: str
    domain: str
    status: str
    issues: List[Dict]
    metrics: Dict
    timestamp: str
    coverage: float
    scores: Dict[str, float]
    audit_info: Dict[str, Any]

class SniffingSystem:
    """Core sniffing system that coordinates all sniffing operations"""

    def __init__(self):
        self.results_cache = {}
        self.active_sniffs = set()
        self.executor = ThreadPoolExecutor(max_workers=SNIFFING_CONFIG.get("max_workers", 4))
        self._setup_directories()
        self._initialize_sniffers()

    def _setup_directories(self):
        """Set up all necessary directories for reports and logs"""
        self.report_dirs = {
            "base": Path("reports/sniffing"),
            "security": Path("reports/sniffing/security"),
            "browser": Path("reports/sniffing/browser"),
            "functional": Path("reports/sniffing/functional"),
            "unit": Path("reports/sniffing/unit"),
            "api": Path("reports/sniffing/api"),
            "documentation": Path("reports/sniffing/documentation"),
            "performance": Path("reports/sniffing/performance"),
            "code_quality": Path("reports/sniffing/code_quality"),
            "audit": Path("reports/sniffing/audit"),
            "logs": Path("logs/sniffing")
        }

        # Create all directories
        for directory in self.report_dirs.values():
            directory.mkdir(parents=True, exist_ok=True)

    def _initialize_sniffers(self):
        """Initialize all domain-specific sniffers"""
        from . import (
            SecuritySniffer, BrowserSniffer, FunctionalSniffer,
            UnitSniffer, ApiSniffer, DocumentationSniffer,
            PerformanceSniffer, CodeQualitySniffer
        )

        self.sniffers = {
            "security": SecuritySniffer(),
            "browser": BrowserSniffer(),
            "functional": FunctionalSniffer(),
            "unit": UnitSniffer(),
            "api": ApiSniffer(),
            "documentation": DocumentationSniffer(),
            "performance": PerformanceSniffer(),
            "code_quality": CodeQualitySniffer()
        }

    async def sniff_file(self, file_path: str, domains: Optional[List[str]] = None) -> SniffResult:
        """Sniff a specific file across specified domains"""
        logger.info(f"Starting sniffing for file: {file_path}")

        if domains is None:
            domains = [domain for domain, config in SNIFFING_CONFIG["domains"].items()
                      if config["enabled"]]

        results = []
        for domain in domains:
            if domain in self.sniffers and SNIFFING_CONFIG["domains"][domain]["enabled"]:
                try:
                    result = await self.sniffers[domain].sniff_file(file_path)
                    results.append(result)
                except Exception as e:
                    logger.error(f"Error in {domain} sniffing for {file_path}: {e}")

        consolidated_result = self._consolidate_results(file_path, results)
        await self._save_result(consolidated_result)
        return consolidated_result

    async def sniff_directory(self, directory: str, domains: Optional[List[str]] = None) -> Dict[str, SniffResult]:
        """Sniff all files in a directory"""
        logger.info(f"Starting directory sniffing: {directory}")

        results = {}
        for root, _, files in os.walk(directory):
            for file in files:
                if self._should_sniff_file(file):
                    file_path = os.path.join(root, file)
                    results[file_path] = await self.sniff_file(file_path, domains)

        await self._generate_directory_report(directory, results)
        return results

    def _should_sniff_file(self, file_name: str) -> bool:
        """Determine if a file should be sniffed based on configuration"""
        return any(
            file_name.endswith(ext)
            for ext in SNIFFING_CONFIG.get("file_extensions", ['.py', '.js', '.ts', '.html', '.css'])
        )

    def _consolidate_results(self, file_path: str, results: List[SniffResult]) -> SniffResult:
        """Consolidate results from multiple domains"""
        all_issues = []
        metrics = {}
        scores = {}
        audit_info = {
            "timestamp": datetime.now().isoformat(),
            "domains_tested": [r.domain for r in results],
            "compliance": self._check_compliance(results)
        }

        for result in results:
            all_issues.extend(result.issues)
            metrics.update(result.metrics)
            scores[result.domain] = result.scores.get(result.domain, 0.0)

        return SniffResult(
            file_path=file_path,
            domain="consolidated",
            status="pass" if not all_issues else "fail",
            issues=all_issues,
            metrics=metrics,
            timestamp=datetime.now().isoformat(),
            coverage=sum(r.coverage for r in results) / len(results) if results else 0.0,
            scores=scores,
            audit_info=audit_info
        )

    def _check_compliance(self, results: List[SniffResult]) -> Dict[str, bool]:
        """Check compliance against various standards"""
        return {
            "soc2": self._check_soc2_compliance(results),
            "security": self._check_security_compliance(results),
            "accessibility": self._check_accessibility_compliance(results)
        }

    async def _save_result(self, result: SniffResult):
        """Save sniffing result to appropriate directories"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save domain-specific result
        if result.domain != "consolidated":
            domain_dir = self.report_dirs[result.domain]
            file_name = f"{Path(result.file_path).stem}_{timestamp}.json"
            with open(domain_dir / file_name, 'w') as f:
                json.dump(self._serialize_result(result), f, indent=2)

        # Save consolidated result
        consolidated_file = self.report_dirs["base"] / f"consolidated_{timestamp}.json"
        with open(consolidated_file, 'w') as f:
            json.dump(self._serialize_result(result), f, indent=2)

        # Save audit information
        if result.audit_info:
            audit_file = self.report_dirs["audit"] / f"audit_{timestamp}.json"
            with open(audit_file, 'w') as f:
                json.dump(result.audit_info, f, indent=2)

    async def _generate_directory_report(self, directory: str, results: Dict[str, SniffResult]):
        """Generate comprehensive report for directory sniffing"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "directory": directory,
            "summary": self._generate_summary(results),
            "compliance": self._check_compliance(list(results.values())),
            "recommendations": self._generate_recommendations(results),
            "audit_trail": self._generate_audit_trail(results)
        }

        # Save report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.report_dirs["base"] / f"directory_report_{timestamp}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)

    def _generate_summary(self, results: Dict[str, SniffResult]) -> Dict:
        """Generate summary of sniffing results"""
        return {
            "total_files": len(results),
            "passed_files": sum(1 for r in results.values() if r.status == "pass"),
            "failed_files": sum(1 for r in results.values() if r.status == "fail"),
            "average_scores": self._calculate_average_scores(results),
            "total_issues": sum(len(r.issues) for r in results.values()),
            "coverage": sum(r.coverage for r in results.values()) / len(results) if results else 0.0
        }

    def _calculate_average_scores(self, results: Dict[str, SniffResult]) -> Dict[str, float]:
        """Calculate average scores across all domains"""
        domain_scores = {}
        for domain in self.sniffers.keys():
            scores = [r.scores.get(domain, 0.0) for r in results.values() if domain in r.scores]
            domain_scores[domain] = sum(scores) / len(scores) if scores else 0.0
        return domain_scores

    def _generate_recommendations(self, results: Dict[str, SniffResult]) -> List[Dict]:
        """Generate actionable recommendations based on sniffing results"""
        recommendations = []
        for file_path, result in results.items():
            if result.status == "fail":
                for issue in result.issues:
                    recommendations.append({
                        "file": file_path,
                        "domain": issue.get("domain", "unknown"),
                        "issue": issue,
                        "recommendation": self._get_recommendation(issue),
                        "priority": self._calculate_priority(issue)
                    })
        return sorted(recommendations, key=lambda x: x["priority"], reverse=True)

    def _generate_audit_trail(self, results: Dict[str, SniffResult]) -> Dict:
        """Generate audit trail for compliance purposes"""
        return {
            "timestamp": datetime.now().isoformat(),
            "sniffing_version": SNIFFING_CONFIG.get("version", "1.0.0"),
            "domains_tested": list(self.sniffers.keys()),
            "files_tested": list(results.keys()),
            "compliance_status": self._check_compliance(list(results.values())),
            "audit_records": [r.audit_info for r in results.values()]
        }

    def _serialize_result(self, result: SniffResult) -> Dict:
        """Serialize SniffResult for JSON storage"""
        return {
            "file_path": str(result.file_path),
            "domain": result.domain,
            "status": result.status,
            "issues": result.issues,
            "metrics": result.metrics,
            "timestamp": result.timestamp,
            "coverage": result.coverage,
            "scores": result.scores,
            "audit_info": result.audit_info
        }

    def _check_soc2_compliance(self, results: List[SniffResult]) -> bool:
        """Check SOC2 compliance based on sniffing results"""
        required_scores = {
            "security": 95.0,
            "audit": 100.0,
            "monitoring": 95.0
        }

        for result in results:
            for domain, required_score in required_scores.items():
                if result.scores.get(domain, 0.0) < required_score:
                    return False
        return True

    def _check_security_compliance(self, results: List[SniffResult]) -> bool:
        """Check security compliance based on sniffing results"""
        for result in results:
            if result.scores.get("security", 0.0) < SNIFFING_CONFIG["domains"]["security"]["thresholds"]["min_security_score"]:
                return False
        return True

    def _check_accessibility_compliance(self, results: List[SniffResult]) -> bool:
        """Check accessibility compliance based on sniffing results"""
        for result in results:
            if "browser" in result.scores and result.scores["browser"] < SNIFFING_CONFIG["domains"]["browser"]["thresholds"]["min_compatibility_score"]:
                return False
        return True

    def _get_recommendation(self, issue: Dict) -> str:
        """Get specific recommendation for an issue"""
        # Implement recommendation logic based on issue type and domain
        return issue.get("recommendation", "No specific recommendation available")

    def _calculate_priority(self, issue: Dict) -> int:
        """Calculate priority for an issue"""
        severity_weights = {
            "critical": 4,
            "high": 3,
            "medium": 2,
            "low": 1
        }
        return severity_weights.get(issue.get("severity", "low"), 1)

async def main():
    """Main function"""
    try:
        sniffer = SniffingSystem()
        results = await sniffer.sniff_directory(".")
        print(f"Sniffing completed. Results saved in {sniffer.report_dirs['base']}")
    except Exception as e:
        logger.error(f"Sniffing failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
