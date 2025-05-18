"""
Git workflow integration for sniffing infrastructure.
"""
import asyncio
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set
import yaml

from ..utils.logging import setup_logger
from ..utils.metrics import MetricsCollector

logger = logging.getLogger(__name__)

class GitWorkflow:
    """Git workflow integration."""

    def __init__(self, config: Dict):
        """Initialize Git workflow.

        Args:
            config: Workflow configuration
        """
        self.config = config

        # Set up logging
        setup_logger(
            logger,
            config["monitoring"]["logging"],
            "git_workflow"
        )

        # Initialize metrics
        self.metrics = MetricsCollector("git_workflow")

        # Initialize state
        self.active_hooks = set()
        self.results_cache = {}

    async def install_hooks(self) -> None:
        """Install Git hooks."""
        try:
            # Get hooks directory
            git_dir = await self._get_git_dir()
            if not git_dir:
                logger.error("Git directory not found")
                return

            hooks_dir = git_dir / "hooks"
            hooks_dir.mkdir(parents=True, exist_ok=True)

            # Install pre-commit hook
            if self.config["git"]["hooks"]["pre_commit"]["enabled"]:
                await self._install_hook(
                    hooks_dir,
                    "pre-commit",
                    self._get_pre_commit_script()
                )

            # Install pre-push hook
            if self.config["git"]["hooks"]["pre_push"]["enabled"]:
                await self._install_hook(
                    hooks_dir,
                    "pre-push",
                    self._get_pre_push_script()
                )

            logger.info("Git hooks installed")

        except Exception as e:
            logger.error(f"Error installing Git hooks: {e}")
            raise

    async def _get_git_dir(self) -> Optional[Path]:
        """Get Git directory.

        Returns:
            Git directory path or None
        """
        try:
            # Start from current directory
            current = Path.cwd()
            while current != current.parent:
                git_dir = current / ".git"
                if git_dir.exists():
                    return git_dir
                current = current.parent

            return None

        except Exception as e:
            logger.error(f"Error getting Git directory: {e}")
            return None

    async def _install_hook(
        self,
        hooks_dir: Path,
        hook_name: str,
        script: str
    ) -> None:
        """Install Git hook.

        Args:
            hooks_dir: Hooks directory
            hook_name: Hook name
            script: Hook script
        """
        try:
            # Create hook file
            hook_file = hooks_dir / hook_name
            with open(hook_file, "w") as f:
                f.write(script)

            # Make executable
            hook_file.chmod(0o755)

            logger.info(f"Installed {hook_name} hook")

        except Exception as e:
            logger.error(f"Error installing {hook_name} hook: {e}")
            raise

    def _get_pre_commit_script(self) -> str:
        """Get pre-commit hook script.

        Returns:
            Hook script
        """
        return """#!/bin/sh
# Pre-commit hook for sniffing infrastructure

# Get staged files
files=$(git diff --cached --name-only --diff-filter=ACM)
if [ -z "$files" ]; then
    exit 0
fi

# Run sniffing
echo "Running pre-commit sniffing..."
python -m sniffing.cli sniff --files "$files" --domains security,functional,unit

# Check result
if [ $? -ne 0 ]; then
    echo "Sniffing failed. Please fix the issues and try again."
    exit 1
fi

exit 0
"""

    def _get_pre_push_script(self) -> str:
        """Get pre-push hook script.

        Returns:
            Hook script
        """
        return """#!/bin/sh
# Pre-push hook for sniffing infrastructure

# Get commits to be pushed
commits=$(git log @{u}.. --pretty=format:%H)
if [ -z "$commits" ]; then
    exit 0
fi

# Get changed files
files=$(git diff --name-only $commits)
if [ -z "$files" ]; then
    exit 0
fi

# Run sniffing
echo "Running pre-push sniffing..."
python -m sniffing.cli sniff --files "$files" --domains security,browser,functional,unit,documentation

# Check result
if [ $? -ne 0 ]; then
    echo "Sniffing failed. Please fix the issues and try again."
    exit 1
fi

exit 0
"""

    async def run_hook(
        self,
        hook_name: str,
        files: List[str]
    ) -> Dict:
        """Run Git hook.

        Args:
            hook_name: Hook name
            files: Files to check

        Returns:
            Hook results
        """
        try:
            # Record metrics
            self.metrics.record_start(f"hook_{hook_name}")
            self.active_hooks.add(hook_name)

            # Get hook config
            hook_config = self.config["git"]["hooks"][hook_name]
            if not hook_config["enabled"]:
                logger.info(f"Hook {hook_name} is disabled")
                return {
                    "status": "skipped",
                    "timestamp": datetime.now().isoformat()
                }

            # Run sniffing
            results = await self._run_sniffing(
                files,
                hook_config["domains"]
            )

            # Check results
            status = "success"
            if any(
                result["status"] == "failed" and
                any(
                    issue["severity"] == "critical"
                    for issue in result["issues"]
                )
                for result in results.values()
            ):
                if hook_config["block_on_critical"]:
                    status = "failed"
                    logger.error(f"Hook {hook_name} failed: Critical issues found")
            elif any(
                result["status"] == "failed" and
                any(
                    issue["severity"] == "high"
                    for issue in result["issues"]
                )
                for result in results.values()
            ):
                if hook_config["block_on_high"]:
                    status = "failed"
                    logger.error(f"Hook {hook_name} failed: High severity issues found")

            # Record metrics
            self.metrics.record_end(
                f"hook_{hook_name}",
                success=(status == "success")
            )

            return {
                "status": status,
                "timestamp": datetime.now().isoformat(),
                "results": results
            }

        except Exception as e:
            logger.error(f"Error running hook {hook_name}: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

        finally:
            if hook_name in self.active_hooks:
                self.active_hooks.remove(hook_name)

    async def _run_sniffing(
        self,
        files: List[str],
        domains: List[str]
    ) -> Dict:
        """Run sniffing on files.

        Args:
            files: Files to check
            domains: Domains to check

        Returns:
            Sniffing results
        """
        try:
            # Import sniffing loop
            from ..base import SniffingLoop
            loop = SniffingLoop(self.config)

            # Run sniffing
            results = {}
            for file in files:
                # Check cache
                cache_key = f"{file}_{','.join(domains)}"
                if cache_key in self.results_cache:
                    results[file] = self.results_cache[cache_key]
                    continue

                # Run sniffing
                result = await loop.sniff_file(file, domains)
                results[file] = result
                self.results_cache[cache_key] = result

            return results

        except Exception as e:
            logger.error(f"Error running sniffing: {e}")
            return {}

    def get_metrics(self) -> Dict:
        """Get workflow metrics.

        Returns:
            Metrics dictionary
        """
        try:
            metrics = {
                "active_hooks": len(self.active_hooks),
                "cached_results": len(self.results_cache)
            }

            # Add collector metrics
            metrics.update(self.metrics.get_metrics())

            return metrics

        except Exception as e:
            logger.error(f"Error getting metrics: {e}")
            return {}
