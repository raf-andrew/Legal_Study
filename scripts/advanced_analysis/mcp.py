#!/usr/bin/env python3
"""
Master Control Program (MCP)
This module orchestrates all analysis, testing, and monitoring activities
"""

import os
import sys
import logging
import time
import json
import asyncio
import aiohttp
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from .config import (
    ANALYSIS_CONFIG,
    GIT_HOOKS,
    MCP_CONFIG,
    SECURITY_SIMULATION,
    FILE_CONFIGS,
    REPORT_CONFIG,
    AI_FEEDBACK
)
from .sniffing import SniffingSystem, SniffResult

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/mcp.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

@dataclass
class AnalysisResult:
    """Data class for analysis results"""
    status: str
    score: float
    issues: List[Dict]
    metrics: Dict
    timestamp: str
    audit_info: Dict[str, Any]

class MasterControlProgram:
    def __init__(self):
        self.results_cache = {}
        self.active_analyses = set()
        self.executor = ThreadPoolExecutor(max_workers=MCP_CONFIG["parallel_jobs"])
        self.last_analysis = {}
        self.sniffing_system = SniffingSystem()
        self.file_watchers = {}
        self.api_endpoints = self._load_api_endpoints()

    async def initialize(self):
        """Initialize the MCP"""
        logger.info("Initializing Master Control Program")
        await self._setup_directories()
        await self._install_dependencies()
        await self._setup_git_hooks()
        await self._verify_environment()
        await self._initialize_sniffing()
        await self._setup_api_monitoring()

    async def _setup_directories(self):
        """Set up required directories"""
        directories = [
            Path("logs"),
            Path("logs/mcp"),
            Path("logs/sniffing"),
            Path("reports"),
            Path("reports/analysis"),
            Path("reports/sniffing"),
            Path("reports/security"),
            Path("reports/audit"),
            Path("reports/api")
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    async def _setup_api_monitoring(self):
        """Set up API endpoint monitoring"""
        self.api_monitor = {
            "endpoints": self.api_endpoints,
            "health_checks": {},
            "last_check": {},
            "metrics": {}
        }

    def _load_api_endpoints(self) -> Dict:
        """Load API endpoint configurations"""
        # Implementation would load from configuration
        return {}

    async def run_sniffing(self, target: str = ".", specific_file: Optional[str] = None, domains: Optional[List[str]] = None):
        """Run comprehensive sniffing"""
        logger.info(f"Starting sniffing on {'specific file: ' + specific_file if specific_file else 'entire codebase'}")

        try:
            if specific_file:
                results = {specific_file: await self.sniffing_system.sniff_file(specific_file, domains)}
            else:
                results = await self.sniffing_system.sniff_directory(target, domains)

            await self._process_sniffing_results(results)
            await self._update_ai_feedback(results)
            await self._trigger_git_hooks(results)

            return results

        except Exception as e:
            logger.error(f"Error in sniffing operation: {e}")
            raise

    async def _process_sniffing_results(self, results: Dict[str, SniffResult]):
        """Process sniffing results and take appropriate actions"""
        consolidated_results = {
            "timestamp": datetime.now().isoformat(),
            "results": {path: vars(result) for path, result in results.items()},
            "summary": {
                "total_files": len(results),
                "passed_files": sum(1 for r in results.values() if r.status == "pass"),
                "failed_files": sum(1 for r in results.values() if r.status == "fail"),
                "compliance": self._check_compliance_status(results)
            }
        }

        # Save results
        await self._save_results(consolidated_results)

        # Update monitoring metrics
        await self._update_monitoring_metrics(consolidated_results)

        # Trigger notifications if needed
        if consolidated_results["summary"]["failed_files"] > 0:
            await self._send_notifications(consolidated_results)

    async def _trigger_git_hooks(self, results: Dict[str, SniffResult]):
        """Trigger appropriate Git hooks based on results"""
        if not self._check_compliance_status(results):
            logger.warning("Compliance check failed - Git operations may be restricted")

        # Update Git hooks based on results
        for hook, config in GIT_HOOKS.items():
            hook_path = Path(".git/hooks") / hook
            if hook_path.exists():
                await self._update_git_hook(hook, results)

    async def monitor_file_changes(self):
        """Monitor for file changes and trigger analysis"""
        class ChangeHandler(FileSystemEventHandler):
            def __init__(self, mcp):
                self.mcp = mcp

            async def on_modified(self, event):
                if not event.is_directory and self.mcp._should_analyze_file(event.src_path):
                    await self.mcp.run_sniffing(specific_file=event.src_path)

        observer = Observer()
        handler = ChangeHandler(self)
        observer.schedule(handler, ".", recursive=True)
        observer.start()

        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
        observer.join()

    async def run_security_simulation(self):
        """Run security attack simulations"""
        logger.info("Starting security simulation")

        # Run security-specific sniffing
        results = await self.run_sniffing(domains=["security"])

        # Run additional security simulations
        for vector in SECURITY_SIMULATION["attack_vectors"]:
            for level in SECURITY_SIMULATION["intensity_levels"]:
                for component in SECURITY_SIMULATION["target_components"]:
                    await self._simulate_attack(vector, level, component)

        return results

    async def _simulate_attack(self, vector: str, level: str, component: str):
        """Simulate a specific security attack"""
        logger.info(f"Simulating {level} {vector} attack on {component}")
        # Implementation would simulate specific attack vectors

    async def monitor_api_endpoints(self):
        """Monitor API endpoints for health and performance"""
        while True:
            try:
                for endpoint, config in self.api_endpoints.items():
                    response = await self._check_endpoint(endpoint)
                    await self._process_api_metrics(endpoint, response)
            except Exception as e:
                logger.error(f"API monitoring error: {e}")
            await asyncio.sleep(MCP_CONFIG.get("api_check_interval", 60))

    async def _check_endpoint(self, endpoint: str) -> Dict:
        """Check health and performance of an API endpoint"""
        async with aiohttp.ClientSession() as session:
            start_time = time.time()
            try:
                async with session.get(endpoint) as response:
                    response_time = time.time() - start_time
                    return {
                        "status": response.status,
                        "response_time": response_time,
                        "timestamp": datetime.now().isoformat()
                    }
            except Exception as e:
                logger.error(f"Error checking endpoint {endpoint}: {e}")
                return {
                    "status": "error",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }

    async def _process_api_metrics(self, endpoint: str, metrics: Dict):
        """Process and store API metrics"""
        self.api_monitor["metrics"][endpoint] = metrics

        # Check for issues
        if metrics["status"] != 200 or metrics.get("response_time", 0) > MCP_CONFIG.get("max_api_response_time", 1.0):
            await self._handle_api_issue(endpoint, metrics)

    async def generate_reports(self):
        """Generate comprehensive reports"""
        logger.info("Generating reports")

        reports = {
            "summary": self._generate_summary_report(),
            "detailed": await self._generate_detailed_report(),
            "trends": await self._generate_trend_report(),
            "recommendations": await self._generate_recommendations(),
            "audit": await self._generate_audit_report()
        }

        await self._save_reports(reports)
        await self._notify_stakeholders(reports)

    def run(self):
        """Main run loop"""
        asyncio.run(self._run_loop())

    async def _run_loop(self):
        """Asynchronous run loop"""
        await self.initialize()

        tasks = [
            self.monitor_file_changes(),
            self.monitor_api_endpoints(),
            self._periodic_analysis(),
            self._periodic_security_check()
        ]

        await asyncio.gather(*tasks)

    async def _periodic_analysis(self):
        """Periodic analysis task"""
        while True:
            try:
                await self.run_sniffing()
                await self.generate_reports()
                await asyncio.sleep(MCP_CONFIG["analysis_interval"])
            except Exception as e:
                logger.error(f"Error in periodic analysis: {e}")
                await asyncio.sleep(60)

    async def _periodic_security_check(self):
        """Periodic security check task"""
        while True:
            try:
                await self.run_security_simulation()
                await asyncio.sleep(MCP_CONFIG.get("security_check_interval", 3600))
            except Exception as e:
                logger.error(f"Error in security check: {e}")
                await asyncio.sleep(60)

    async def run_sniffing_loop(self, target: str = ".", interval: int = None):
        """Run continuous sniffing loop"""
        logger.info("Starting sniffing loop")

        try:
            while True:
                # Run comprehensive sniffing
                results = await self.run_sniffing(target)

                # Process and store results
                await self._process_sniffing_results(results)

                # Update AI feedback
                await self._update_ai_feedback(results)

                # Check Git workflow integration
                await self._check_git_workflow(results)

                # Wait for interval
                await asyncio.sleep(interval or MCP_CONFIG["analysis_interval"])

        except asyncio.CancelledError:
            logger.info("Sniffing loop cancelled")
        except Exception as e:
            logger.error(f"Error in sniffing loop: {e}")
            raise

    async def run_file_specific_sniffing(self, file_path: str, domains: Optional[List[str]] = None):
        """Run sniffing on a specific file"""
        logger.info(f"Running file-specific sniffing on {file_path}")

        try:
            # Run sniffing on specific file
            results = await self.sniffing_system.sniff_file(file_path, domains)

            # Process results
            await self._process_file_results(file_path, results)

            return results

        except Exception as e:
            logger.error(f"Error in file-specific sniffing: {e}")
            raise

    async def _process_file_results(self, file_path: str, results: Dict):
        """Process results for a specific file"""
        try:
            # Save results
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_file = self.report_dirs["sniffing"] / f"{Path(file_path).stem}_{timestamp}.json"

            with open(report_file, 'w') as f:
                json.dump({
                    "timestamp": timestamp,
                    "file_path": file_path,
                    "results": results,
                    "summary": {
                        "status": results["status"],
                        "total_issues": len(results["issues"]),
                        "scores": results["scores"]
                    }
                }, f, indent=2)

            # Check thresholds and trigger actions
            if results["status"] == "fail":
                await self._handle_failed_sniffing(file_path, results)

        except Exception as e:
            logger.error(f"Error processing file results: {e}")
            raise

    async def _handle_failed_sniffing(self, file_path: str, results: Dict):
        """Handle failed sniffing results"""
        try:
            # Group issues by domain
            issues_by_domain = {}
            for issue in results["issues"]:
                domain = issue["domain"]
                if domain not in issues_by_domain:
                    issues_by_domain[domain] = []
                issues_by_domain[domain].append(issue)

            # Generate domain-specific reports
            for domain, issues in issues_by_domain.items():
                report_file = self.report_dirs[domain] / f"{Path(file_path).stem}_issues.json"
                with open(report_file, 'w') as f:
                    json.dump({
                        "timestamp": datetime.now().isoformat(),
                        "file_path": file_path,
                        "domain": domain,
                        "issues": issues
                    }, f, indent=2)

            # Send notifications if configured
            if self.config.get("notification", {}).get("enabled", False):
                await self._send_issue_notifications(file_path, results)

        except Exception as e:
            logger.error(f"Error handling failed sniffing: {e}")
            raise

    async def _check_git_workflow(self, results: Dict):
        """Check Git workflow integration"""
        try:
            # Check if any critical issues
            has_critical = any(
                issue["severity"] == "critical"
                for result in results.values()
                for issue in result["issues"]
            )

            # Update Git hooks based on results
            git_config = self.config.get("git_integration", {})
            if git_config.get("enabled", False):
                hook_path = Path(".git/hooks")

                # Update pre-commit hook
                if git_config.get("pre_commit", {}).get("enabled", False):
                    await self._update_git_hook("pre-commit", has_critical)

                # Update pre-push hook
                if git_config.get("pre_push", {}).get("enabled", False):
                    await self._update_git_hook("pre-push", has_critical)

        except Exception as e:
            logger.error(f"Error checking Git workflow: {e}")
            raise

    async def _update_git_hook(self, hook_name: str, has_critical: bool):
        """Update Git hook based on sniffing results"""
        try:
            hook_path = Path(".git/hooks") / hook_name

            # Create hook if it doesn't exist
            if not hook_path.exists():
                hook_content = f"""#!/bin/sh
# Generated by MCP
python -m scripts.advanced_analysis.manage_sniffing .
if [ $? -ne 0 ]; then
    echo "Sniffing checks failed"
    exit 1
fi
"""
                hook_path.write_text(hook_content)
                hook_path.chmod(0o755)

            # Update hook status
            if has_critical:
                logger.warning(f"Critical issues found - {hook_name} hook will block")

        except Exception as e:
            logger.error(f"Error updating Git hook: {e}")
            raise

    async def _send_issue_notifications(self, file_path: str, results: Dict):
        """Send notifications about issues"""
        try:
            notification_config = self.config.get("notification", {})

            # Prepare notification content
            content = {
                "timestamp": datetime.now().isoformat(),
                "file_path": file_path,
                "status": results["status"],
                "total_issues": len(results["issues"]),
                "critical_issues": sum(1 for i in results["issues"] if i["severity"] == "critical"),
                "high_issues": sum(1 for i in results["issues"] if i["severity"] == "high")
            }

            # Send to configured channels
            if notification_config.get("slack_webhook"):
                await self._send_slack_notification(content)

            if notification_config.get("email"):
                await self._send_email_notification(content)

        except Exception as e:
            logger.error(f"Error sending notifications: {e}")
            raise

def main():
    """Main function"""
    try:
        mcp = MasterControlProgram()
        mcp.run()
    except Exception as e:
        logger.error(f"MCP failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
