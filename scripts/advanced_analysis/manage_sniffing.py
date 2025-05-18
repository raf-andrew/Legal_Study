#!/usr/bin/env python3
"""
Sniffing Management Script
This script provides a CLI interface for managing sniffing operations
"""

import os
import sys
import logging
import asyncio
import argparse
import json
from pathlib import Path
from typing import List, Optional, Dict
from datetime import datetime

from .sniffing import SniffingSystem
from .config import SNIFFING_CONFIG, MCP_CONFIG

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/sniffing_manager.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class SniffingManager:
    """Manager class for sniffing operations"""

    def __init__(self):
        self.sniffing_system = SniffingSystem()
        self.report_dir = Path("reports/sniffing")
        self.report_dir.mkdir(parents=True, exist_ok=True)

    async def run_sniffing(self, target: str, domains: Optional[List[str]] = None,
                          continuous: bool = False, interval: int = None):
        """Run sniffing operations"""
        try:
            while True:
                if os.path.isfile(target):
                    results = await self.sniffing_system.sniff_file(target, domains)
                    await self._process_results({target: results})
                else:
                    results = await self.sniffing_system.sniff_directory(target, domains)
                    await self._process_results(results)

                if not continuous:
                    break

                await asyncio.sleep(interval or MCP_CONFIG["analysis_interval"])

        except KeyboardInterrupt:
            logger.info("Sniffing operation interrupted by user")
        except Exception as e:
            logger.error(f"Error in sniffing operation: {e}")
            raise

    async def _process_results(self, results: Dict):
        """Process and report sniffing results"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Generate summary
        summary = self._generate_summary(results)
        logger.info(f"Sniffing Summary: {json.dumps(summary, indent=2)}")

        # Save detailed results
        report_file = self.report_dir / f"sniffing_report_{timestamp}.json"
        with open(report_file, 'w') as f:
            json.dump({
                "timestamp": timestamp,
                "summary": summary,
                "results": {k: self._serialize_result(v) for k, v in results.items()}
            }, f, indent=2)

        # Generate recommendations if issues found
        if summary["failed_files"] > 0:
            await self._generate_recommendations(results)

    def _generate_summary(self, results: Dict) -> Dict:
        """Generate summary of sniffing results"""
        return {
            "total_files": len(results),
            "passed_files": sum(1 for r in results.values() if r.status == "pass"),
            "failed_files": sum(1 for r in results.values() if r.status == "fail"),
            "domains_tested": list(set(r.domain for r in results.values())),
            "average_scores": self._calculate_average_scores(results),
            "compliance_status": self._check_compliance(results)
        }

    def _calculate_average_scores(self, results: Dict) -> Dict:
        """Calculate average scores across all domains"""
        scores = {}
        for domain in SNIFFING_CONFIG["domains"]:
            domain_scores = [r.scores.get(domain, 0.0) for r in results.values()
                           if domain in r.scores]
            if domain_scores:
                scores[domain] = sum(domain_scores) / len(domain_scores)
        return scores

    def _check_compliance(self, results: Dict) -> Dict:
        """Check compliance status"""
        compliance = {
            "soc2": True,
            "security": True,
            "accessibility": True
        }

        for result in results.values():
            if result.status == "fail":
                for issue in result.issues:
                    if issue.get("severity", "low") in ["critical", "high"]:
                        compliance["security"] = False
                    if issue.get("type") == "accessibility":
                        compliance["accessibility"] = False

        return compliance

    async def _generate_recommendations(self, results: Dict):
        """Generate and save recommendations"""
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

        # Sort recommendations by priority
        recommendations.sort(key=lambda x: x["priority"], reverse=True)

        # Save recommendations
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        recommendations_file = self.report_dir / f"recommendations_{timestamp}.json"
        with open(recommendations_file, 'w') as f:
            json.dump({
                "timestamp": timestamp,
                "recommendations": recommendations
            }, f, indent=2)

    def _get_recommendation(self, issue: Dict) -> str:
        """Get specific recommendation for an issue"""
        domain = issue.get("domain", "unknown")
        issue_type = issue.get("type", "unknown")

        recommendations = {
            "security": {
                "vulnerability": "Fix security vulnerability by following security best practices",
                "authentication": "Implement proper authentication mechanisms",
                "authorization": "Implement proper authorization controls"
            },
            "browser": {
                "compatibility": "Ensure cross-browser compatibility",
                "responsive": "Implement responsive design patterns",
                "accessibility": "Follow WCAG guidelines for accessibility"
            },
            "performance": {
                "response_time": "Optimize code for better performance",
                "memory_usage": "Reduce memory consumption",
                "cpu_usage": "Optimize CPU intensive operations"
            }
        }

        return recommendations.get(domain, {}).get(issue_type, issue.get("recommendation", "No specific recommendation"))

    def _calculate_priority(self, issue: Dict) -> int:
        """Calculate priority for an issue"""
        severity_weights = {
            "critical": 4,
            "high": 3,
            "medium": 2,
            "low": 1
        }
        return severity_weights.get(issue.get("severity", "low"), 1)

    def _serialize_result(self, result) -> Dict:
        """Serialize result for JSON storage"""
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

async def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Manage sniffing operations")
    parser.add_argument("target", help="File or directory to sniff")
    parser.add_argument("--domains", nargs="+", help="Specific domains to sniff")
    parser.add_argument("--continuous", action="store_true", help="Run continuously")
    parser.add_argument("--interval", type=int, help="Interval between runs (seconds)")

    args = parser.parse_args()

    try:
        manager = SniffingManager()
        await manager.run_sniffing(
            args.target,
            domains=args.domains,
            continuous=args.continuous,
            interval=args.interval
        )
    except Exception as e:
        logger.error(f"Sniffing management failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
