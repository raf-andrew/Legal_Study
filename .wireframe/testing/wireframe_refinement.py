#!/usr/bin/env python3

import os
import sys
import json
import logging
from datetime import datetime
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional
import subprocess
import time
import argparse
from dataclasses import dataclass
from enum import Enum
import re
import ssl
import urllib.request
import stat

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('wireframe_refinement.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class RefinementStatus:
    """Enum for refinement status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

class RefinementState:
    """Class to represent the state of a refinement iteration."""
    def __init__(self, iteration: int = 0, wireframe_path: Optional[str] = None,
                 analysis_results: Optional[Dict[str, Any]] = None, tag: Optional[str] = None):
        self.iteration = iteration
        self.wireframe_path = wireframe_path
        self.analysis_results = analysis_results or {}
        self.timestamp = datetime.now().isoformat()
        self.tag = tag
        self.status = RefinementStatus.PENDING

    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary for JSON serialization."""
        return {
            "iteration": self.iteration,
            "wireframe_path": self.wireframe_path,
            "analysis_results": self.analysis_results,
            "timestamp": self.timestamp,
            "tag": self.tag,
            "status": self.status
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RefinementState':
        """Create state from dictionary."""
        state = cls(
            iteration=data.get("iteration", 0),
            wireframe_path=data.get("wireframe_path"),
            analysis_results=data.get("analysis_results", {}),
            tag=data.get("tag")
        )
        state.timestamp = data.get("timestamp", datetime.now().isoformat())
        state.status = data.get("status", RefinementStatus.PENDING)
        return state

@dataclass
class RefinementSnapshot:
    timestamp: str
    state: RefinementState
    test_results: Dict[str, Any]
    analysis_results: Dict[str, Any]
    wireframe_files: List[str]
    tag: Optional[str] = None

class VersionTracker:
    """Class to track versions and their relationships."""
    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)
        self.versions_dir = self.base_dir / "versions"
        self.screenshots_dir = self.base_dir / "screenshots"
        self.logs_dir = self.base_dir / "logs"
        self.versions = {}
        self.current_version = None
        self.original_wireframe = None

        # Create necessary directories
        for directory in [self.versions_dir, self.screenshots_dir, self.logs_dir]:
            directory.mkdir(exist_ok=True)

        # Initialize logging
        self.logger = logging.getLogger("version_tracker")
        self.logger.setLevel(logging.INFO)

        # Add file handler
        log_file = self.logs_dir / "version_tracking.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        self.logger.addHandler(file_handler)

    def set_original_wireframe(self, wireframe_path: str) -> None:
        """Set the original wireframe path.
        Args:
            wireframe_path: Path to the original wireframe file
        """
        self.original_wireframe = wireframe_path
        self.logger.info(f"Set original wireframe: {wireframe_path}")

        # Update metadata for v1 if it exists
        if "v1" in self.versions:
            metadata = self.versions["v1"]
            metadata["is_original"] = True
            metadata["wireframe_path"] = wireframe_path
            metadata_path = os.path.join(self.versions_dir, "v1", "metadata.json")
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)

    def create_version(self, wireframe_path: str, version_id: Optional[str] = None) -> str:
        """Create a new version of the wireframe.
        Args:
            wireframe_path: Path to the wireframe file
            version_id: Optional version ID (will be generated if not provided)
        Returns:
            str: Version ID of the created version
        """
        if not os.path.exists(wireframe_path):
            raise FileNotFoundError(f"Wireframe file not found: {wireframe_path}")

        if version_id is None:
            version_id = f"v{len(self.versions) + 1}"

        version_dir = os.path.join(self.versions_dir, version_id)
        os.makedirs(version_dir, exist_ok=True)

        # Copy wireframe to version directory
        dest_path = os.path.join(version_dir, os.path.basename(wireframe_path))
        shutil.copy2(wireframe_path, dest_path)

        # Create metadata
        metadata = {
            "version_id": version_id,
            "created_at": datetime.now().isoformat(),
            "wireframe_path": wireframe_path,  # Store original path
            "version_path": dest_path,  # Store versioned path
            "is_original": version_id == "v1" or wireframe_path == self.original_wireframe,
            "improvements": [],
            "rejected_improvements": [],
            "screenshots": [],
            "parent_version": None if version_id == "v1" else self.current_version
        }

        # Save metadata
        metadata_path = os.path.join(version_dir, "metadata.json")
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)

        self.versions[version_id] = metadata
        self.current_version = version_id

        return version_id

    def add_improvement(self, version_id: str, improvement: Dict[str, Any]) -> None:
        """Add an improvement to a version."""
        if version_id not in self.versions:
            raise ValueError(f"Version {version_id} not found")

        # Ensure improvement has required fields
        if not all(k in improvement for k in ["type", "suggestion", "priority"]):
            raise ValueError("Improvement must have type, suggestion, and priority")

        # Add improvement to version
        self.versions[version_id]["improvements"].append(improvement)
        self.logger.info(f"Added improvement to version {version_id}")

    def add_rejected_improvement(self, version_id: str, improvement: Dict[str, Any]) -> None:
        """Add a rejected improvement to a version."""
        if version_id not in self.versions:
            raise ValueError(f"Version {version_id} not found")

        # Ensure improvement has required fields
        if not all(k in improvement for k in ["type", "suggestion", "priority"]):
            raise ValueError("Improvement must have type, suggestion, and priority")

        # Add rejected improvement to version
        self.versions[version_id]["rejected_improvements"].append(improvement)
        self.logger.info(f"Added rejected improvement to version {version_id}")

    def get_improvement_history(self, version_id: str) -> Dict[str, List[Dict[str, Any]]]:
        """Get improvement history for a version."""
        if version_id not in self.versions:
            raise ValueError(f"Version {version_id} not found")

        return {
            "accepted": self.versions[version_id]["improvements"],
            "rejected": self.versions[version_id]["rejected_improvements"]
        }

    def get_version_metadata(self, version_id: str) -> dict:
        if version_id not in self.versions:
            raise ValueError(f"Version {version_id} not found")
        return self.versions[version_id]

    def add_screenshot(self, version_id: str, screenshot_path: str, viewport: dict) -> None:
        version = self.get_version_metadata(version_id)
        if "screenshots" not in version:
            version["screenshots"] = []
        screenshot_meta = {
            "path": screenshot_path,
            "viewport": viewport,
            "timestamp": datetime.now().isoformat()
        }
        version["screenshots"].append(screenshot_meta)
        self.logger.info(f"Added screenshot to version {version_id}")

    def add_step(self, version_id: str, step_type: str, details: dict) -> None:
        version = self.get_version_metadata(version_id)
        if "steps" not in version:
            version["steps"] = []
        step = {
            "type": step_type,
            "timestamp": datetime.now().isoformat(),
            "details": details
        }
        version["steps"].append(step)
        self.logger.info(f"Added step to version {version_id}")

    def get_version_history(self) -> List[Dict[str, Any]]:
        """Get complete version history."""
        return self.versions

    def cleanup(self) -> None:
        """Clean up resources."""
        for handler in self.logger.handlers[:]:
            handler.close()
            self.logger.removeHandler(handler)

    def flush_reports(self):
        """Clear all refinement history and reports."""
        # Flush version tracker reports
        self.flush_reports()

        # Clear improvement history
        self.improvements = []
        self.rejected_improvements = []

        # Clear analysis results
        self.analysis_results = {}

        # Clear test results
        self.test_results = {}

        logger.info("All refinement history and reports cleared")

class WireframeRefinementLoop:
    """Class to handle wireframe refinement process."""
    def __init__(self):
        """Initialize the refinement loop."""
        self.logger = logging.getLogger(__name__)
        self.current_iteration = 0
        self.current_wireframe = None
        self.analysis_results = {}
        self.version_tracker = None
        self.original_wireframe = None

        # Default configuration
        self.config = {
            "max_iterations": 10,
            "viewport_sizes": [
                {"name": "desktop", "width": 1920, "height": 1080},
                {"name": "tablet", "width": 768, "height": 1024},
                {"name": "mobile", "width": 375, "height": 667}
            ],
            "security_settings": {
                "min_file_permissions": 0o600,
                "max_file_permissions": 0o644,
                "allowed_extensions": [".html", ".css", ".js", ".json", ".png", ".jpg", ".jpeg", ".gif"],
                "max_file_size": 10 * 1024 * 1024,  # 10MB
                "required_ssl_version": "TLSv1.2",
                "allowed_ciphers": [
                    "ECDHE-ECDSA-AES128-GCM-SHA256",
                    "ECDHE-RSA-AES128-GCM-SHA256",
                    "ECDHE-ECDSA-AES256-GCM-SHA384",
                    "ECDHE-RSA-AES256-GCM-SHA384"
                ]
            },
            "analysis_settings": {
                "content_density": {"min": 0.3, "max": 0.7, "weight": 1.0},
                "color_contrast": {"min_ratio": 4.5, "weight": 1.0},
                "responsive_design": {"breakpoints": [320, 768, 1024, 1440], "weight": 1.0}
            }
        }

    def setup(self, base_dir: str) -> None:
        """Set up the refinement loop.

        Args:
            base_dir: Base directory for output files
        """
        self.base_dir = Path(base_dir).resolve()
        self.version_tracker = VersionTracker(str(self.base_dir))
        self.config = self.load_config()
        self.current_wireframe = None
        self.screenshot_dir = str(self.version_tracker.screenshots_dir)

        # Configure logging
        log_file = self.base_dir / "wireframe_refinement.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        self.logger.addHandler(file_handler)

        self.logger.info(f"Setup complete. Base directory: {self.base_dir}")

    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file."""
        config_path = Path("config.json").resolve()
        if not config_path.exists():
            self.logger.warning(f"Config file not found at {config_path}, using defaults")
            return {
                "viewport_sizes": [
                    {"name": "Desktop", "width": 1920, "height": 1080},
                    {"name": "Tablet", "width": 768, "height": 1024},
                    {"name": "Mobile", "width": 375, "height": 667}
                ],
                "analysis_checks": [
                    {"name": "Content Density", "type": "density"},
                    {"name": "Accessibility", "type": "accessibility"},
                    {"name": "Visual Hierarchy", "type": "hierarchy"}
                ],
                "analysis_settings": {
                    "content_density": {"min": 0.3, "max": 0.7, "weight": 1.0},
                    "color_contrast": {"min_ratio": 4.5, "weight": 1.0},
                    "responsive_design": {"breakpoints": [320, 768, 1024, 1440], "weight": 1.0}
                }
            }

        try:
            with open(config_path) as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Error loading config: {e}")
            raise

    def validate_file(self, file_path: str) -> bool:
        """Validate file permissions, size, and extension."""
        config = self.load_config()
        security_settings = config["security_settings"]

        # Check file size
        file_size = os.path.getsize(file_path)
        max_size = security_settings["max_file_size"]
        if file_size > max_size:
            raise ValueError(f"File size exceeds maximum limit of {max_size} bytes")

        # Check file extension
        file_ext = os.path.splitext(file_path)[1].lower()
        if file_ext not in security_settings["allowed_extensions"]:
            raise ValueError(f"File extension {file_ext} not allowed")

        # Check file permissions
        file_stat = os.stat(file_path)
        permissions = oct(file_stat.st_mode & 0o777)
        min_perms = int(security_settings["min_file_permissions"], 8)
        max_perms = int(security_settings["max_file_permissions"], 8)

        if not (min_perms <= int(permissions, 8) <= max_perms):
            raise ValueError(f"File permissions {permissions} outside allowed range")

        return True

    def configure_ssl(self) -> ssl.SSLContext:
        """Configure SSL context with security settings."""
        config = self.load_config()
        security_settings = config["security_settings"]

        context = ssl.create_default_context()
        context.minimum_version = getattr(ssl, f"PROTOCOL_{security_settings['required_ssl_version']}")
        context.set_ciphers(":".join(security_settings["allowed_ciphers"]))
        context.verify_mode = ssl.CERT_REQUIRED
        context.check_hostname = True

        return context

    def sanitize_input(self, input_str: str) -> str:
        """Sanitize user input to prevent security issues."""
        # Remove script tags
        input_str = re.sub(r'<script.*?>.*?</script>', '', input_str, flags=re.DOTALL | re.IGNORECASE)
        # Remove path traversal attempts
        input_str = re.sub(r'\.\./|\.\.\\', '', input_str)
        # Remove SQL injection attempts (common patterns)
        input_str = re.sub(r"(['\"]\s*OR\s*['\"]?\d+['\"]?=\d+)|(['\"]\s*OR\s*['\"]?1['\"]?=['\"]?1)|(['\"]\s*--)", '', input_str, flags=re.IGNORECASE)
        input_str = re.sub(r"' OR '1'='1", '', input_str, flags=re.IGNORECASE)
        # Remove PHP tags
        input_str = re.sub(r'<\?php.*?\?>', '', input_str, flags=re.DOTALL | re.IGNORECASE)
        return input_str

    def run_cursor_analysis(self, wireframe_path: str) -> Dict[str, Any]:
        """Run Cursor CLI analysis on wireframe."""
        try:
            result = subprocess.run(
                ["cursor", "analyze", wireframe_path],
                capture_output=True,
                text=True,
                check=True
            )
            return json.loads(result.stdout)
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Cursor analysis failed: {e}")
            raise
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse Cursor analysis output: {e}")
            raise

    def create_snapshot(self, tag: Optional[str] = None) -> RefinementState:
        """Create a snapshot of the current state. (Filenames are made Windows-safe)"""
        state = RefinementState(
            iteration=self.current_iteration,
            wireframe_path=self.current_wireframe,
            analysis_results=self.analysis_results.copy(),
            tag=tag
        )
        snapshot_dir = os.path.join(self.test_dir, "snapshots")
        os.makedirs(snapshot_dir, exist_ok=True)
        # Sanitize timestamp for Windows filenames
        safe_timestamp = state.timestamp.replace(":", "-")
        snapshot_path = os.path.join(snapshot_dir, f"snapshot_{safe_timestamp}.json")
        with open(snapshot_path, 'w') as f:
            json.dump(state.to_dict(), f)
        return state

    def restore_snapshot(self, snapshot_path: str) -> None:
        """Restore state from a snapshot."""
        with open(snapshot_path, 'r') as f:
            data = json.load(f)
            state = RefinementState.from_dict(data)

        self.current_iteration = state.iteration
        self.current_wireframe = state.wireframe_path
        self.analysis_results = state.analysis_results.copy()

    def create_version(self, wireframe_path: str, version_id: Optional[str] = None) -> str:
        """Create a new version of the wireframe.

        Args:
            wireframe_path: Path to the wireframe file
            version_id: Optional version ID

        Returns:
            Version ID
        """
        wireframe_path = Path(wireframe_path).resolve()
        if not wireframe_path.exists():
            raise FileNotFoundError(f"Wireframe file not found: {wireframe_path}")

        version_id = version_id or f"v{len(self.version_tracker.versions)}"
        version_dir = self.version_tracker.versions_dir / version_id
        version_dir.mkdir(exist_ok=True)

        # Copy wireframe file
        dest_path = version_dir / "wireframe.html"
        shutil.copy2(wireframe_path, dest_path)

        # Create metadata
        metadata = {
            "version_id": version_id,
            "wireframe_path": str(dest_path),
            "created_at": datetime.now().isoformat(),
            "is_original": version_id == "v1" or wireframe_path == self.version_tracker.original_wireframe,
            "improvements": [],
            "rejected_improvements": [],
            "parent_version": None if version_id == "v1" else self.version_tracker.current_version,
            "screenshots": []
        }

        with open(version_dir / "metadata.json", "w") as f:
            json.dump(metadata, f, indent=2)

        self.version_tracker.versions[version_id] = metadata
        self.logger.info(f"Created version {version_id}")
        self.version_tracker.current_version = version_id
        return version_id

    def capture_screenshots(self, wireframe_path: str, version_id: str) -> List[str]:
        """Capture screenshots of the wireframe at different viewport sizes.
        Args:
            wireframe_path: Path to the wireframe file
            version_id: ID of the version
        Returns:
            List[str]: Paths to the captured screenshots
        """
        viewports = [
            {"width": 320, "height": 480, "name": "mobile"},
            {"width": 768, "height": 1024, "name": "tablet"},
            {"width": 1024, "height": 768, "name": "desktop"}
        ]

        screenshots = []
        for viewport in viewports:
            screenshot_name = f"{version_id}_{viewport['name']}.png"
            screenshot_path = os.path.join(self.screenshot_dir, screenshot_name)

            # Create screenshot file
            with open(screenshot_path, 'w') as f:
                f.write(f"Mock screenshot for {viewport['name']} viewport")

            # Add screenshot to version metadata
            self.version_tracker.add_screenshot(version_id, screenshot_path, viewport)
            screenshots.append(screenshot_path)

        return screenshots

    def analyze_version(self, version_id: str, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Analyze a version using Cursor CLI."""
        version_meta = self.version_tracker.get_version_metadata(version_id)
        wireframe_path = version_meta["wireframe_path"]

        # Use provided config or load default
        if config is None:
            config = self.load_config()

        # Run Cursor CLI analysis
        try:
            result = subprocess.run(
                ["cursor", "analyze", wireframe_path],
                capture_output=True,
                text=True,
                check=True
            )

            # Parse analysis results
            analysis = json.loads(result.stdout)

            # Add analysis step to version
            self.version_tracker.add_step(version_id, "analysis", {
                "results": analysis,
                "config": config
            })

            return analysis

        except subprocess.CalledProcessError as e:
            self.logger.error(f"Analysis failed: {e}")
            raise
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse analysis results: {e}")
            raise

    def generate_report(self, version_id: str) -> str:
        """Generate a report for a specific version.
        Args:
            version_id: ID of the version to generate report for
        Returns:
            str: Path to the generated report
        """
        version_meta = self.version_tracker.get_version_metadata(version_id)
        if not version_meta:
            raise ValueError(f"Version {version_id} not found")

        report_dir = os.path.join(self.version_tracker.versions_dir, version_id)
        report_path = os.path.join(report_dir, "report.html")

        # Generate HTML report
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Wireframe Refinement Report - {version_id}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .section {{ margin-bottom: 20px; }}
                .improvement {{ margin: 10px 0; padding: 10px; border-left: 3px solid #ccc; }}
                .high-priority {{ border-left-color: #ff4444; }}
                .medium-priority {{ border-left-color: #ffbb33; }}
                .low-priority {{ border-left-color: #00C851; }}
            </style>
        </head>
        <body>
            <h1>Wireframe Refinement Report</h1>
            <div class="section">
                <h2>Version Information</h2>
                <p>Version ID: {version_id}</p>
                <p>Created: {version_meta["created_at"]}</p>
                <p>Original Wireframe: {version_meta["wireframe_path"]}</p>
                <p>Version Path: {version_meta["version_path"]}</p>
            </div>
        """

        # Add improvements section
        if version_meta["improvements"]:
            html_content += """
            <div class="section">
                <h2>Improvements</h2>
            """
            for improvement in version_meta["improvements"]:
                priority_class = f"{improvement['priority']}-priority"
                message = improvement.get('message', improvement.get('suggestion', ''))
                html_content += f"""
                <div class="improvement {priority_class}">
                    <h3>{improvement['type']}</h3>
                    <p>{message}</p>
                </div>
                """
            html_content += "</div>"

        # Add rejected improvements section
        if version_meta["rejected_improvements"]:
            html_content += """
            <div class="section">
                <h2>Rejected Improvements</h2>
            """
            for improvement in version_meta["rejected_improvements"]:
                priority_class = f"{improvement['priority']}-priority"
                message = improvement.get('message', improvement.get('suggestion', ''))
                html_content += f"""
                <div class="improvement {priority_class}">
                    <h3>{improvement['type']}</h3>
                    <p>{message}</p>
                </div>
                """
            html_content += "</div>"

        # Add screenshots section
        if version_meta["screenshots"]:
            html_content += """
            <div class="section">
                <h2>Screenshots</h2>
            """
            for screenshot in version_meta["screenshots"]:
                html_content += f"""
                <div class="screenshot">
                    <h3>{screenshot['viewport']['name']}</h3>
                    <img src="{os.path.basename(screenshot['path'])}" alt="{screenshot['viewport']['name']} viewport">
                </div>
                """
            html_content += "</div>"

        html_content += """
        </body>
        </html>
        """

        with open(report_path, 'w') as f:
            f.write(html_content)

        return report_path

    def _run_feature_tests(self, version_id: str) -> List[Dict[str, Any]]:
        """Run feature tests on a version.
        Args:
            version_id: The version ID to test
        Returns:
            List[Dict[str, Any]]: List of test results
        """
        # For testing purposes, return mock test results
        return [
            {
                "name": "Content Density Test",
                "status": "passed",
                "score": 0.85,
                "message": "Content density is within acceptable range"
            },
            {
                "name": "Color Contrast Test",
                "status": "passed",
                "score": 0.92,
                "message": "All color combinations meet WCAG guidelines"
            },
            {
                "name": "Responsive Layout Test",
                "status": "passed",
                "score": 0.88,
                "message": "Layout adapts correctly to different viewport sizes"
            }
        ]

    def _generate_feature_tests_html(self, tests: List[Dict[str, Any]]) -> str:
        """Generate HTML for feature test results.

        Args:
            tests: List of test results

        Returns:
            str: HTML representation of test results
        """
        if not tests:
            return "<p>No tests run</p>"

        html = []
        for test in tests:
            html.append(f"""
                <div class="test-result {test['status']}">
                    <h4>{test['name']}</h4>
                    <p>{test['message']}</p>
                </div>
            """)

        return "\n".join(html)

    def _generate_diff_view(self, before_version: str, after_version: str) -> str:
        """Generate HTML diff view between versions.

        Args:
            before_version: Version ID of the before state
            after_version: Version ID of the after state

        Returns:
            str: HTML representation of the diff
        """
        before_meta = self.version_tracker.get_version_metadata(before_version)
        after_meta = self.version_tracker.get_version_metadata(after_version)

        try:
            result = subprocess.run(
                ["cursor", "diff",
                 before_meta["wireframe_path"],
                 after_meta["wireframe_path"]],
                capture_output=True,
                text=True,
                check=True
            )

            diff_lines = result.stdout.splitlines()
            html = []
            for line in diff_lines:
                if line.startswith("+"):
                    html.append(f'<div class="diff-line added">{line}</div>')
                elif line.startswith("-"):
                    html.append(f'<div class="diff-line removed">{line}</div>')
                else:
                    html.append(f'<div class="diff-line">{line}</div>')

            return "\n".join(html)

        except subprocess.CalledProcessError as e:
            return f"<p>Failed to generate diff: {e.stderr}</p>"

    def _generate_screenshot_html(self, version_id: Optional[str]) -> str:
        """Generate HTML for version screenshots."""
        if not version_id:
            return ""

        version_meta = self.version_tracker.get_version_metadata(version_id)
        screenshots_html = []

        for screenshot in version_meta["screenshots"]:
            screenshots_html.append(f"""
                <div>
                    <h3>{screenshot['viewport']['name']}</h3>
                    <img src="{screenshot['path']}" class="screenshot">
                </div>
            """)

        return "\n".join(screenshots_html)

    def _generate_improvements_html(self, improvements: List[Dict[str, Any]], rejected: bool = False) -> str:
        """Generate HTML for improvements list."""
        if not improvements:
            return "<p>No improvements</p>"

        html = []
        for improvement in improvements:
            html.append(f"""
                <div class="improvement {improvement['priority']} {rejected and 'rejected' or ''}">
                    <h4>{improvement['type'].replace('_', ' ').title()}</h4>
                    <p>{improvement['suggestion']}</p>
                    <small>Priority: {improvement['priority']}</small>
                </div>
            """)

        return "\n".join(html)

    def run_refinement_loop(self, wireframe_path: str, max_iterations: int = 10,
                          skip_user_interaction: bool = False) -> Dict[str, Any]:
        """Run the refinement loop.
        Args:
            wireframe_path: Path to the wireframe file
            max_iterations: Maximum number of iterations
            skip_user_interaction: Whether to skip user interaction
        Returns:
            Dict[str, Any]: Results of the refinement process
        """
        self.original_wireframe = wireframe_path
        self.version_tracker.set_original_wireframe(wireframe_path)

        # Ensure analysis_settings is always the correct nested structure
        self.config["analysis_settings"] = {
            "content_density": {"min": 0.3, "max": 0.7, "weight": 1.0},
            "color_contrast": {"min_ratio": 4.5, "weight": 1.0},
            "responsive_design": {"breakpoints": [320, 768, 1024, 1440], "weight": 1.0}
        }

        results = {
            "versions": [],
            "improvements": [],
            "screenshots": []
        }

        for iteration in range(max_iterations):
            self.logger.info(f"Starting iteration {iteration + 1}/{max_iterations}")

            # Create version
            version_id = self.version_tracker.create_version(wireframe_path, f"iteration_{iteration}")
            results["versions"].append(version_id)

            # Capture screenshots
            screenshots = self.capture_screenshots(wireframe_path, version_id)
            results["screenshots"].extend(screenshots)

            # Analyze version
            analysis = self.analyze_version(version_id)

            # Generate improvements
            improvements = self._generate_improvements(analysis)
            results["improvements"].extend(improvements)

            # Apply improvements
            if improvements:
                wireframe_path = self._apply_improvements(wireframe_path, improvements)

            if not skip_user_interaction:
                # In a real scenario, we would ask for user feedback here
                pass

        return results

    def _generate_improvements(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate improvement suggestions based on analysis results.
        Args:
            analysis: Analysis results dictionary
        Returns:
            List[Dict[str, Any]]: List of improvement suggestions
        """
        improvements = []

        # Check content density
        if analysis.get("content_density", 0) < self.config["analysis_settings"]["content_density"]["min"]:
            improvements.append({
                "type": "content_density",
                "message": "Content density is too low. Consider adding more content or reducing whitespace.",
                "priority": "high"
            })
        elif analysis.get("content_density", 0) > self.config["analysis_settings"]["content_density"]["max"]:
            improvements.append({
                "type": "content_density",
                "message": "Content density is too high. Consider reducing content or increasing whitespace.",
                "priority": "high"
            })

        # Check color contrast
        if analysis.get("color_contrast", 0) < self.config["analysis_settings"]["color_contrast"]["min_ratio"]:
            improvements.append({
                "type": "color_contrast",
                "message": "Color contrast ratio is below WCAG guidelines. Consider adjusting color combinations.",
                "priority": "high"
            })

        # Check responsive design
        responsive_score = analysis.get("responsive_design", {}).get("score", 0)
        if responsive_score < 0.8:
            improvements.append({
                "type": "responsive_design",
                "message": "Responsive design needs improvement. Check layout at different viewport sizes.",
                "priority": "medium"
            })

        return improvements

    def _apply_improvements(self, wireframe_path: str, improvements: List[Dict[str, Any]]) -> str:
        """Apply improvements to the wireframe."""
        with open(wireframe_path, 'r') as f:
            content = f.read()

        # Apply each improvement
        for improvement in improvements:
            if improvement["type"] == "content_density":
                # Add placeholder content
                content = content.replace("</body>", "<div class='content-block'>Additional content for density</div></body>")
            elif improvement["type"] == "line_length":
                # Break long lines
                content = re.sub(r'(.{100})', r'\1\n', content)
            elif improvement["type"] == "color_count":
                # Replace colors with a limited palette
                content = re.sub(r'#[0-9a-fA-F]{6}', '#000000', content)

        # Write modified content
        new_path = wireframe_path.replace(".html", "_improved.html")
        with open(new_path, 'w') as f:
            f.write(content)

        return new_path

    def _revert_to_version(self, version_id: str) -> str:
        """Revert to a specific version."""
        version_meta = self.version_tracker.get_version_metadata(version_id)
        return version_meta["wireframe_path"]

    def cleanup(self) -> None:
        """Clean up resources."""
        self.version_tracker.cleanup()

    def flush_reports(self):
        """Clear all refinement history and reports."""
        # Flush version tracker reports
        self.version_tracker.flush_reports()

        # Clear improvement history
        self.improvements = []
        self.rejected_improvements = []

        # Clear analysis results
        self.analysis_results = {}

        # Clear test results
        self.test_results = {}

        logger.info("All refinement history and reports cleared")

def main():
    parser = argparse.ArgumentParser(description='Wireframe Refinement Process')
    parser.add_argument('--wireframe-path', required=True, help='Path to the wireframe file')
    parser.add_argument('--max-iterations', type=int, default=10, help='Maximum number of refinement iterations')
    parser.add_argument('--skip-user-interaction', action='store_true', help='Skip user interaction and auto-accept changes')
    parser.add_argument('--config', default='config.json', help='Path to configuration file')
    parser.add_argument('--output-dir', required=True, help='Directory to store output files')

    args = parser.parse_args()

    # Create output directory if it doesn't exist
    os.makedirs(args.output_dir, exist_ok=True)

    # Initialize refinement loop
    refinement_loop = WireframeRefinementLoop()
    refinement_loop.setup(args.output_dir)

    try:
        # Run refinement loop
        results = refinement_loop.run_refinement_loop(
            wireframe_path=args.wireframe_path,
            max_iterations=args.max_iterations,
            skip_user_interaction=args.skip_user_interaction
        )

        # Print summary
        print("\nRefinement Process Summary:")
        print(f"Status: {results['status']}")
        print(f"Iterations completed: {results['iterations']}")
        print(f"Versions created: {len(results['versions'])}")
        print(f"Improvements applied: {len(results['improvements'])}")
        print(f"Screenshots captured: {len(results['screenshots'])}")

        # Open the final report in browser
        if results['status'] == 'completed':
            report_path = os.path.join(args.output_dir, 'versions', f"v{results['iterations']}", 'report.html')
            if os.path.exists(report_path):
                import webbrowser
                webbrowser.open(f'file://{os.path.abspath(report_path)}')

    except Exception as e:
        print(f"Error during refinement process: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()
