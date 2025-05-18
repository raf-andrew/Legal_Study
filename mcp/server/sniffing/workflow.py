"""
Git workflow integration for sniffing operations.
"""
import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from ...utils.config import MCPConfig
from ...utils.git import GitIntegration
from ...utils.logging import setup_logger
from ...utils.metrics import record_job_start, record_job_end

logger = logging.getLogger("git_workflow")

class GitWorkflow:
    """Manages Git workflow integration."""

    def __init__(self, config: MCPConfig):
        """Initialize Git workflow.

        Args:
            config: MCP configuration
        """
        self.config = config
        self.git = GitIntegration(config)
        self.hooks = {}
        self.active_jobs = set()
        self.hook_queue = asyncio.Queue()
        self.is_running = False
        self._setup_logging()
        self._setup_hooks()

    def _setup_logging(self) -> None:
        """Set up logging for Git workflow."""
        setup_logger(logger, self.config.logging_config, "git_workflow")

    def _setup_hooks(self) -> None:
        """Set up Git hooks."""
        try:
            # Get workspace path
            workspace = Path(self.config.workspace_path)
            hooks_dir = workspace / ".git" / "hooks"

            # Create hook scripts
            self._create_hook(hooks_dir, "pre-commit")
            self._create_hook(hooks_dir, "pre-push")

            logger.info("Git hooks set up successfully")

        except Exception as e:
            logger.error(f"Error setting up Git hooks: {e}")

    def _create_hook(self, hooks_dir: Path, hook_name: str) -> None:
        """Create Git hook script.

        Args:
            hooks_dir: Hooks directory
            hook_name: Hook name
        """
        try:
            # Create hook script
            hook_path = hooks_dir / hook_name
            hook_script = f"""#!/bin/sh
# MCP {hook_name} hook
curl -X POST http://localhost:{self.config.api_port}/api/v1/git/{hook_name} \\
    -H "Content-Type: application/json" \\
    -d @- <<EOF
{{
    "files": $(git diff --cached --name-only | jq -R -s -c 'split("\\n")[:-1]')
}}
EOF
"""
            # Write script
            with open(hook_path, "w") as f:
                f.write(hook_script)

            # Make executable
            hook_path.chmod(0o755)

            logger.info(f"Created {hook_name} hook")

        except Exception as e:
            logger.error(f"Error creating {hook_name} hook: {e}")

    async def start(self) -> None:
        """Start Git workflow."""
        try:
            logger.info("Starting Git workflow")
            self.is_running = True

            # Start hook worker
            hook_worker = asyncio.create_task(self._hook_worker())
            await hook_worker

        except Exception as e:
            logger.error(f"Error starting Git workflow: {e}")
            self.is_running = False

    async def stop(self) -> None:
        """Stop Git workflow."""
        try:
            logger.info("Stopping Git workflow")
            self.is_running = False

            # Wait for queue to empty
            await self.hook_queue.join()

            # Wait for jobs to complete
            while self.active_jobs:
                await asyncio.sleep(0.1)

            logger.info("Git workflow stopped")

        except Exception as e:
            logger.error(f"Error stopping Git workflow: {e}")

    async def pre_commit(self, files: List[str]) -> Dict[str, Any]:
        """Run pre-commit sniffing.

        Args:
            files: Changed files

        Returns:
            Pre-commit results
        """
        try:
            # Create job ID
            job_id = f"pre_commit_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self.active_jobs.add(job_id)

            try:
                # Record job start
                record_job_start("git_workflow", "pre_commit")

                # Add to queue
                await self.hook_queue.put({
                    "id": job_id,
                    "type": "pre-commit",
                    "files": files,
                    "timestamp": datetime.now()
                })

                # Wait for result
                while job_id in self.active_jobs:
                    await asyncio.sleep(0.1)

                # Get result
                result = self.hooks.get(job_id, {
                    "status": "failed",
                    "error": "Job not found"
                })

                # Record job end
                record_job_end(
                    "git_workflow",
                    "pre_commit",
                    datetime.now().timestamp() - result["timestamp"].timestamp(),
                    result["status"] == "success"
                )

                return result

            finally:
                self.active_jobs.remove(job_id)

        except Exception as e:
            logger.error(f"Error in pre-commit hook: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now()
            }

    async def pre_push(self, files: List[str]) -> Dict[str, Any]:
        """Run pre-push validation.

        Args:
            files: Changed files

        Returns:
            Pre-push results
        """
        try:
            # Create job ID
            job_id = f"pre_push_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self.active_jobs.add(job_id)

            try:
                # Record job start
                record_job_start("git_workflow", "pre_push")

                # Add to queue
                await self.hook_queue.put({
                    "id": job_id,
                    "type": "pre-push",
                    "files": files,
                    "timestamp": datetime.now()
                })

                # Wait for result
                while job_id in self.active_jobs:
                    await asyncio.sleep(0.1)

                # Get result
                result = self.hooks.get(job_id, {
                    "status": "failed",
                    "error": "Job not found"
                })

                # Record job end
                record_job_end(
                    "git_workflow",
                    "pre_push",
                    datetime.now().timestamp() - result["timestamp"].timestamp(),
                    result["status"] == "success"
                )

                return result

            finally:
                self.active_jobs.remove(job_id)

        except Exception as e:
            logger.error(f"Error in pre-push hook: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now()
            }

    async def _hook_worker(self) -> None:
        """Process hooks from queue."""
        try:
            while self.is_running:
                # Get hook from queue
                hook = await self.hook_queue.get()
                hook_id = hook["id"]
                hook_type = hook["type"]
                files = hook["files"]

                try:
                    # Process hook
                    if hook_type == "pre-commit":
                        result = await self._process_pre_commit(files)
                    elif hook_type == "pre-push":
                        result = await self._process_pre_push(files)
                    else:
                        result = {
                            "status": "failed",
                            "error": f"Unknown hook type: {hook_type}",
                            "timestamp": datetime.now()
                        }

                    # Store result
                    self.hooks[hook_id] = result

                except Exception as e:
                    logger.error(f"Error processing {hook_type} hook: {e}")
                    self.hooks[hook_id] = {
                        "status": "failed",
                        "error": str(e),
                        "timestamp": datetime.now()
                    }

                finally:
                    # Mark task as done
                    self.hook_queue.task_done()

        except Exception as e:
            logger.error(f"Error in hook worker: {e}")

    async def _process_pre_commit(self, files: List[str]) -> Dict[str, Any]:
        """Process pre-commit hook.

        Args:
            files: Changed files

        Returns:
            Hook results
        """
        try:
            # Run sniffing
            from ..core import MCPServer
            server = MCPServer(self.config)
            results = await server.sniff({
                "files": files,
                "domains": ["security", "functional", "unit"],
                "priority": 1
            })

            # Check results
            has_critical = False
            for domain in results.get("domains", {}).values():
                for issue in domain.get("issues", []):
                    if issue.get("severity") == "critical":
                        has_critical = True
                        break
                if has_critical:
                    break

            return {
                "status": "failed" if has_critical else "success",
                "results": results,
                "timestamp": datetime.now()
            }

        except Exception as e:
            logger.error(f"Error processing pre-commit hook: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now()
            }

    async def _process_pre_push(self, files: List[str]) -> Dict[str, Any]:
        """Process pre-push hook.

        Args:
            files: Changed files

        Returns:
            Hook results
        """
        try:
            # Run sniffing
            from ..core import MCPServer
            server = MCPServer(self.config)
            results = await server.sniff({
                "files": files,
                "domains": ["security", "functional", "unit", "documentation"],
                "priority": 1
            })

            # Check results
            has_critical = False
            has_high = False
            for domain in results.get("domains", {}).values():
                for issue in domain.get("issues", []):
                    severity = issue.get("severity")
                    if severity == "critical":
                        has_critical = True
                        break
                    elif severity == "high":
                        has_high = True
                if has_critical:
                    break

            # Check configuration
            block_critical = self.config.git.get("block_on_critical", True)
            block_high = self.config.git.get("block_on_high", False)

            return {
                "status": "failed"
                if (block_critical and has_critical) or (block_high and has_high)
                else "success",
                "results": results,
                "timestamp": datetime.now()
            }

        except Exception as e:
            logger.error(f"Error processing pre-push hook: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now()
            }

    def get_metrics(self) -> Dict[str, Any]:
        """Get workflow metrics.

        Returns:
            Metrics dictionary
        """
        try:
            return {
                "active_jobs": len(self.active_jobs),
                "queued_hooks": self.hook_queue.qsize(),
                "stored_hooks": len(self.hooks),
                "git_status": self.git.get_status()
            }

        except Exception as e:
            logger.error(f"Error getting metrics: {e}")
            return {}
