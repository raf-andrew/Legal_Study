#!/usr/bin/env python3
"""
Platform Build Script
This script automates the build process for the platform.
"""

import os
import sys
import json
import logging
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('build.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class PlatformBuilder:
    """Platform build orchestrator."""

    def __init__(self):
        """Initialize the builder."""
        self.reports_dir = Path("reports")
        self.reports_dir.mkdir(exist_ok=True)
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "build_steps": {},
            "issues": []
        }

    def build_platform(self) -> bool:
        """Run all build steps."""
        logger.info("Starting platform build...")
        
        try:
            # Run pre-build checks
            self._run_pre_build_checks()
            
            # Build Python components
            self._build_python_components()
            
            # Build Node.js components
            self._build_node_components()
            
            # Build documentation
            self._build_documentation()
            
            # Run post-build checks
            self._run_post_build_checks()
            
            # Generate reports
            self._generate_reports()
            
            return len(self.results["issues"]) == 0
            
        except Exception as e:
            logger.error(f"Error during build: {str(e)}")
            self.results["issues"].append({
                "type": "system_error",
                "message": str(e)
            })
            return False

    def _run_pre_build_checks(self):
        """Run pre-build checks."""
        logger.info("Running pre-build checks...")
        
        try:
            # Check Python version
            python_version = subprocess.run([
                "python", "--version"
            ], check=True, capture_output=True, text=True)
            
            # Check Node.js version
            node_version = subprocess.run([
                "node", "--version"
            ], check=True, capture_output=True, text=True)
            
            # Check npm version
            npm_version = subprocess.run([
                "npm", "--version"
            ], check=True, capture_output=True, text=True)
            
            # Check git status
            git_status = subprocess.run([
                "git", "status", "--porcelain"
            ], check=True, capture_output=True, text=True)
            
            self.results["build_steps"]["pre_build_checks"] = {
                "status": "success",
                "details": {
                    "python_version": python_version.stdout.strip(),
                    "node_version": node_version.stdout.strip(),
                    "npm_version": npm_version.stdout.strip(),
                    "git_status": "clean" if not git_status.stdout else "dirty"
                }
            }
        except Exception as e:
            self._add_issue("pre_build_error", f"Pre-build checks failed: {str(e)}")

    def _build_python_components(self):
        """Build Python components."""
        logger.info("Building Python components...")
        
        try:
            # Run tests
            subprocess.run([
                "venv/Scripts/pytest" if os.name == "nt" else "venv/bin/pytest",
                "tests",
                "-v",
                "--junitxml=reports/test-results.xml"
            ], check=True, capture_output=True)
            
            # Build Python package
            subprocess.run([
                "venv/Scripts/python" if os.name == "nt" else "venv/bin/python",
                "setup.py",
                "bdist_wheel"
            ], check=True, capture_output=True)
            
            self.results["build_steps"]["python_build"] = {
                "status": "success",
                "details": {
                    "tests": "passed",
                    "package": "built"
                }
            }
        except Exception as e:
            self._add_issue("python_build_error", f"Python build failed: {str(e)}")

    def _build_node_components(self):
        """Build Node.js components."""
        logger.info("Building Node.js components...")
        
        try:
            # Run tests
            subprocess.run([
                "npm", "test"
            ], check=True, capture_output=True)
            
            # Build frontend
            subprocess.run([
                "npm", "run", "build"
            ], check=True, capture_output=True)
            
            self.results["build_steps"]["node_build"] = {
                "status": "success",
                "details": {
                    "tests": "passed",
                    "frontend": "built"
                }
            }
        except Exception as e:
            self._add_issue("node_build_error", f"Node.js build failed: {str(e)}")

    def _build_documentation(self):
        """Build documentation."""
        logger.info("Building documentation...")
        
        try:
            # Build API documentation
            subprocess.run([
                "venv/Scripts/sphinx-build" if os.name == "nt" else "venv/bin/sphinx-build",
                "-b",
                "html",
                "docs/source",
                "docs/build/html"
            ], check=True, capture_output=True)
            
            # Build TypeScript documentation
            subprocess.run([
                "npx",
                "typedoc",
                "--out",
                "docs/build/ts",
                "src"
            ], check=True, capture_output=True)
            
            self.results["build_steps"]["documentation"] = {
                "status": "success",
                "details": {
                    "api_docs": "built",
                    "ts_docs": "built"
                }
            }
        except Exception as e:
            self._add_issue("documentation_error", f"Documentation build failed: {str(e)}")

    def _run_post_build_checks(self):
        """Run post-build checks."""
        logger.info("Running post-build checks...")
        
        try:
            # Check build artifacts
            dist_dir = Path("dist")
            build_dir = Path("build")
            docs_dir = Path("docs/build")
            
            self.results["build_steps"]["post_build_checks"] = {
                "status": "success",
                "details": {
                    "dist_exists": dist_dir.exists(),
                    "build_exists": build_dir.exists(),
                    "docs_exists": docs_dir.exists(),
                    "wheel_files": len(list(dist_dir.glob("*.whl"))),
                    "doc_files": len(list(docs_dir.rglob("*.html")))
                }
            }
        except Exception as e:
            self._add_issue("post_build_error", f"Post-build checks failed: {str(e)}")

    def _add_issue(self, issue_type: str, message: str):
        """Add an issue to the results."""
        self.results["issues"].append({
            "type": issue_type,
            "message": message
        })

    def _generate_reports(self):
        """Generate build reports."""
        logger.info("Generating reports...")
        
        # Save JSON report
        with open("reports/build.json", "w") as f:
            json.dump(self.results, f, indent=2)
        
        # Generate HTML report
        self._generate_html_report()
        
        # Generate summary
        self._generate_summary()

    def _generate_html_report(self):
        """Generate HTML report."""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Platform Build Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .summary {{ background-color: #f5f5f5; padding: 20px; border-radius: 5px; }}
                .step {{ margin: 10px 0; padding: 10px; border-radius: 3px; }}
                .success {{ background-color: #dff0d8; }}
                .error {{ background-color: #f2dede; }}
                .timestamp {{ color: #666; }}
            </style>
        </head>
        <body>
            <h1>Platform Build Report</h1>
            <p class="timestamp">Generated at: {self.results['timestamp']}</p>
            
            <div class="summary">
                <h2>Summary</h2>
                <p>Total Steps: {len(self.results['build_steps'])}</p>
                <p>Successful Steps: {sum(1 for s in self.results['build_steps'].values() if s['status'] == 'success')}</p>
                <p>Failed Steps: {sum(1 for s in self.results['build_steps'].values() if s['status'] == 'error')}</p>
                <p>Total Issues: {len(self.results['issues'])}</p>
            </div>

            <h2>Build Steps</h2>
        """
        
        for step, result in self.results["build_steps"].items():
            status = result["status"]
            html += f"""
            <div class="step {status}">
                <h3>{step.replace('_', ' ').title()}</h3>
                <p>Status: {status.title()}</p>
                <pre>{json.dumps(result.get('details', {}), indent=2)}</pre>
            </div>
            """
        
        html += """
        </body>
        </html>
        """
        
        with open("reports/build.html", "w") as f:
            f.write(html)

    def _generate_summary(self):
        """Generate summary report."""
        summary = f"""
        Platform Build Summary
        Generated at: {self.results['timestamp']}
        
        Total Steps: {len(self.results['build_steps'])}
        Successful Steps: {sum(1 for s in self.results['build_steps'].values() if s['status'] == 'success')}
        Failed Steps: {sum(1 for s in self.results['build_steps'].values() if s['status'] == 'error')}
        Total Issues: {len(self.results['issues'])}
        
        Issues:
        """
        
        for issue in self.results["issues"]:
            summary += f"\n- {issue['type']}: {issue['message']}"
        
        with open("reports/build_summary.txt", "w") as f:
            f.write(summary)

def main():
    """Main entry point."""
    builder = PlatformBuilder()
    success = builder.build_platform()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 