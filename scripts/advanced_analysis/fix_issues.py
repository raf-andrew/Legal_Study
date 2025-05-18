#!/usr/bin/env python3
"""
Issue Fixing Script
This script helps manage and fix issues identified by the sniffing system
"""

import os
import sys
import logging
import asyncio
import json
import argparse
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

from .config import SNIFFING_CONFIG
from .sniffing import SniffingSystem
from .mcp import MasterControlProgram

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/fix_issues.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class IssueFixer:
    """Manages issue fixing workflow"""

    def __init__(self):
        self.mcp = MasterControlProgram()
        self.sniffing_system = SniffingSystem()
        self.report_dir = Path("reports/fixes")
        self.report_dir.mkdir(parents=True, exist_ok=True)

    async def initialize(self):
        """Initialize the issue fixer"""
        await self.mcp.initialize()

    async def fix_issues(self, target: str, domains: Optional[List[str]] = None,
                        interactive: bool = True):
        """Fix issues in target file or directory"""
        logger.info(f"Starting issue fixing for {target}")

        try:
            # Run initial sniffing
            results = await self.mcp.run_sniffing(target, domains)

            # Process and fix issues
            fixed_issues = await self._process_and_fix_issues(target, results, interactive)

            # Generate fix report
            await self._generate_fix_report(target, results, fixed_issues)

            # Run verification sniffing
            verification_results = await self.mcp.run_sniffing(target, domains)

            return {
                "initial_results": results,
                "fixed_issues": fixed_issues,
                "verification_results": verification_results
            }

        except Exception as e:
            logger.error(f"Error fixing issues: {e}")
            raise

    async def _process_and_fix_issues(self, target: str, results: Dict,
                                    interactive: bool) -> List[Dict]:
        """Process and fix identified issues"""
        fixed_issues = []

        try:
            # Sort issues by severity
            all_issues = []
            for file_results in results.values():
                for issue in file_results["issues"]:
                    all_issues.append({
                        "file_path": file_results["file_path"],
                        **issue
                    })

            sorted_issues = sorted(
                all_issues,
                key=lambda x: {
                    "critical": 0,
                    "high": 1,
                    "medium": 2,
                    "low": 3
                }.get(x["severity"], 4)
            )

            # Process each issue
            for issue in sorted_issues:
                if interactive:
                    if not await self._confirm_fix(issue):
                        continue

                fixed = await self._fix_issue(issue)
                if fixed:
                    fixed_issues.append({
                        "issue": issue,
                        "fixed_at": datetime.now().isoformat(),
                        "verification": await self._verify_fix(issue["file_path"])
                    })

        except Exception as e:
            logger.error(f"Error processing and fixing issues: {e}")
            raise

        return fixed_issues

    async def _confirm_fix(self, issue: Dict) -> bool:
        """Get user confirmation for fix"""
        print("\nIssue Details:")
        print(f"Severity: {issue['severity']}")
        print(f"Type: {issue['type']}")
        print(f"Description: {issue['description']}")
        print(f"File: {issue['file_path']}")
        print(f"Recommendation: {issue['recommendation']}")

        response = input("\nFix this issue? (y/n): ")
        return response.lower() == 'y'

    async def _fix_issue(self, issue: Dict) -> bool:
        """Fix a specific issue"""
        try:
            # Get appropriate fixer based on issue type
            fixer = self._get_issue_fixer(issue["type"])
            if not fixer:
                logger.warning(f"No fixer available for issue type: {issue['type']}")
                return False

            # Apply fix
            fixed = await fixer(issue)

            if fixed:
                logger.info(f"Successfully fixed issue: {issue['type']} in {issue['file_path']}")
            else:
                logger.warning(f"Failed to fix issue: {issue['type']} in {issue['file_path']}")

            return fixed

        except Exception as e:
            logger.error(f"Error fixing issue: {e}")
            return False

    def _get_issue_fixer(self, issue_type: str):
        """Get appropriate fixer function for issue type"""
        fixers = {
            "style": self._fix_style_issue,
            "complexity": self._fix_complexity_issue,
            "maintainability": self._fix_maintainability_issue,
            "security": self._fix_security_issue,
            "performance": self._fix_performance_issue,
            "documentation": self._fix_documentation_issue
        }
        return fixers.get(issue_type)

    async def _fix_style_issue(self, issue: Dict) -> bool:
        """Fix style-related issues"""
        try:
            with open(issue["file_path"], 'r') as f:
                content = f.read()

            # Apply style fixes based on issue details
            if "line_length" in issue:
                content = self._fix_line_length(content)
            elif "naming_convention" in issue:
                content = self._fix_naming_convention(content)

            with open(issue["file_path"], 'w') as f:
                f.write(content)

            return True

        except Exception as e:
            logger.error(f"Error fixing style issue: {e}")
            return False

    async def _fix_complexity_issue(self, issue: Dict) -> bool:
        """Fix complexity-related issues"""
        try:
            with open(issue["file_path"], 'r') as f:
                content = f.read()

            # Apply complexity fixes based on issue details
            if "cyclomatic_complexity" in issue:
                content = self._reduce_complexity(content)
            elif "nested_loops" in issue:
                content = self._fix_nested_loops(content)

            with open(issue["file_path"], 'w') as f:
                f.write(content)

            return True

        except Exception as e:
            logger.error(f"Error fixing complexity issue: {e}")
            return False

    async def _fix_maintainability_issue(self, issue: Dict) -> bool:
        """Fix maintainability-related issues"""
        try:
            with open(issue["file_path"], 'r') as f:
                content = f.read()

            # Apply maintainability fixes based on issue details
            if "function_length" in issue:
                content = self._split_long_function(content)
            elif "class_size" in issue:
                content = self._split_large_class(content)

            with open(issue["file_path"], 'w') as f:
                f.write(content)

            return True

        except Exception as e:
            logger.error(f"Error fixing maintainability issue: {e}")
            return False

    async def _fix_security_issue(self, issue: Dict) -> bool:
        """Fix security-related issues"""
        try:
            with open(issue["file_path"], 'r') as f:
                content = f.read()

            # Apply security fixes based on issue details
            if "vulnerability" in issue:
                content = self._fix_vulnerability(content)
            elif "authentication" in issue:
                content = self._fix_authentication(content)

            with open(issue["file_path"], 'w') as f:
                f.write(content)

            return True

        except Exception as e:
            logger.error(f"Error fixing security issue: {e}")
            return False

    async def _fix_performance_issue(self, issue: Dict) -> bool:
        """Fix performance-related issues"""
        try:
            with open(issue["file_path"], 'r') as f:
                content = f.read()

            # Apply performance fixes based on issue details
            if "slow_function" in issue:
                content = self._optimize_function(content)
            elif "resource_usage" in issue:
                content = self._optimize_resources(content)

            with open(issue["file_path"], 'w') as f:
                f.write(content)

            return True

        except Exception as e:
            logger.error(f"Error fixing performance issue: {e}")
            return False

    async def _fix_documentation_issue(self, issue: Dict) -> bool:
        """Fix documentation-related issues"""
        try:
            with open(issue["file_path"], 'r') as f:
                content = f.read()

            # Apply documentation fixes based on issue details
            if "missing_docstring" in issue:
                content = self._add_docstring(content)
            elif "incomplete_docstring" in issue:
                content = self._complete_docstring(content)

            with open(issue["file_path"], 'w') as f:
                f.write(content)

            return True

        except Exception as e:
            logger.error(f"Error fixing documentation issue: {e}")
            return False

    async def _verify_fix(self, file_path: str) -> Dict:
        """Verify fix by running sniffing again"""
        try:
            results = await self.mcp.run_file_specific_sniffing(file_path)
            return {
                "status": results["status"],
                "remaining_issues": len(results["issues"]),
                "scores": results["scores"]
            }
        except Exception as e:
            logger.error(f"Error verifying fix: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    async def _generate_fix_report(self, target: str, initial_results: Dict,
                                 fixed_issues: List[Dict]):
        """Generate report of fixing activity"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_file = self.report_dir / f"fix_report_{timestamp}.json"

            report = {
                "timestamp": datetime.now().isoformat(),
                "target": target,
                "initial_issues": sum(len(r["issues"]) for r in initial_results.values()),
                "fixed_issues": len(fixed_issues),
                "fixes": fixed_issues,
                "summary": {
                    "critical_fixed": sum(1 for f in fixed_issues
                                       if f["issue"]["severity"] == "critical"),
                    "high_fixed": sum(1 for f in fixed_issues
                                    if f["issue"]["severity"] == "high"),
                    "medium_fixed": sum(1 for f in fixed_issues
                                      if f["issue"]["severity"] == "medium"),
                    "low_fixed": sum(1 for f in fixed_issues
                                   if f["issue"]["severity"] == "low")
                }
            }

            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2)

        except Exception as e:
            logger.error(f"Error generating fix report: {e}")
            raise

async def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Fix issues identified by sniffing")
    parser.add_argument("target", help="File or directory to fix")
    parser.add_argument("--domains", nargs="+", help="Specific domains to fix")
    parser.add_argument("--non-interactive", action="store_true",
                       help="Run without user confirmation")

    args = parser.parse_args()

    try:
        fixer = IssueFixer()
        await fixer.initialize()
        results = await fixer.fix_issues(
            args.target,
            domains=args.domains,
            interactive=not args.non_interactive
        )
        print(json.dumps(results, indent=2))
    except Exception as e:
        logger.error(f"Issue fixing failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
