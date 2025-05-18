"""
MCP CI/CD integration utilities.
"""
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import aiohttp
import yaml

logger = logging.getLogger("mcp_ci_cd")

class CICDIntegration:
    """CI/CD integration manager."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize CI/CD integration.

        Args:
            config: CI/CD configuration
        """
        self.config = config
        self.session = None
        self.active_jobs: Set[str] = set()
        self.metrics: Dict[str, Any] = {}

    async def start(self) -> None:
        """Start CI/CD integration."""
        try:
            logger.info("Starting CI/CD integration...")
            self.session = aiohttp.ClientSession()
            logger.info("CI/CD integration started successfully")

        except Exception as e:
            logger.error(f"Error starting CI/CD integration: {e}")
            raise

    async def stop(self) -> None:
        """Stop CI/CD integration."""
        try:
            logger.info("Stopping CI/CD integration...")
            if self.session:
                await self.session.close()
            self.active_jobs.clear()
            self.metrics.clear()
            logger.info("CI/CD integration stopped successfully")

        except Exception as e:
            logger.error(f"Error stopping CI/CD integration: {e}")
            raise

    async def run_pipeline(
        self,
        pipeline: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Run CI/CD pipeline.

        Args:
            pipeline: Pipeline configuration
            context: Pipeline context

        Returns:
            Pipeline results
        """
        try:
            # Create job ID
            job_id = f"job_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self.active_jobs.add(job_id)

            try:
                # Initialize results
                results = {
                    "id": job_id,
                    "status": "running",
                    "timestamp": datetime.now(),
                    "stages": {}
                }

                # Run stages
                for stage_name, stage in pipeline.get("stages", {}).items():
                    stage_results = await self._run_stage(stage_name, stage, context)
                    results["stages"][stage_name] = stage_results

                    # Check if stage failed
                    if stage_results["status"] == "failed":
                        if stage.get("fail_fast", True):
                            break

                # Update status
                results["status"] = "completed"
                if any(
                    stage["status"] == "failed"
                    for stage in results["stages"].values()
                ):
                    results["status"] = "failed"

                # Update metrics
                self._update_metrics(results)

                return results

            finally:
                self.active_jobs.remove(job_id)

        except Exception as e:
            logger.error(f"Error running pipeline: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now()
            }

    async def _run_stage(
        self,
        stage_name: str,
        stage: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Run pipeline stage.

        Args:
            stage_name: Stage name
            stage: Stage configuration
            context: Pipeline context

        Returns:
            Stage results
        """
        try:
            # Initialize results
            results = {
                "name": stage_name,
                "status": "running",
                "timestamp": datetime.now(),
                "steps": {}
            }

            # Run steps
            for step_name, step in stage.get("steps", {}).items():
                step_results = await self._run_step(step_name, step, context)
                results["steps"][step_name] = step_results

                # Check if step failed
                if step_results["status"] == "failed":
                    if step.get("fail_fast", True):
                        break

            # Update status
            results["status"] = "completed"
            if any(
                step["status"] == "failed"
                for step in results["steps"].values()
            ):
                results["status"] = "failed"

            return results

        except Exception as e:
            logger.error(f"Error running stage: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now()
            }

    async def _run_step(
        self,
        step_name: str,
        step: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Run pipeline step.

        Args:
            step_name: Step name
            step: Step configuration
            context: Pipeline context

        Returns:
            Step results
        """
        try:
            # Initialize results
            results = {
                "name": step_name,
                "status": "running",
                "timestamp": datetime.now()
            }

            # Get step type
            step_type = step.get("type")
            if not step_type:
                raise ValueError(f"Missing step type: {step_name}")

            # Run step
            if step_type == "sniff":
                results.update(await self._run_sniff_step(step, context))
            elif step_type == "analyze":
                results.update(await self._run_analyze_step(step, context))
            elif step_type == "fix":
                results.update(await self._run_fix_step(step, context))
            elif step_type == "test":
                results.update(await self._run_test_step(step, context))
            elif step_type == "deploy":
                results.update(await self._run_deploy_step(step, context))
            else:
                raise ValueError(f"Unknown step type: {step_type}")

            return results

        except Exception as e:
            logger.error(f"Error running step: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now()
            }

    async def _run_sniff_step(
        self,
        step: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Run sniff step.

        Args:
            step: Step configuration
            context: Pipeline context

        Returns:
            Step results
        """
        try:
            # Get files
            files = step.get("files", context.get("files", []))
            if not files:
                raise ValueError("No files to sniff")

            # Get domains
            domains = step.get("domains", context.get("domains", []))
            if not domains:
                raise ValueError("No domains to sniff")

            # Run sniffing
            from ..server.orchestrator import MCPOrchestrator
            orchestrator = MCPOrchestrator(self.config)
            job_id = await orchestrator.schedule_job(
                "sniff",
                files,
                domains,
                priority=step.get("priority", 0)
            )

            # Wait for results
            while True:
                status = await orchestrator.get_job_status(job_id)
                if status["status"] in ["completed", "failed"]:
                    break
                await asyncio.sleep(1)

            return status

        except Exception as e:
            logger.error(f"Error running sniff step: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now()
            }

    async def _run_analyze_step(
        self,
        step: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Run analyze step.

        Args:
            step: Step configuration
            context: Pipeline context

        Returns:
            Step results
        """
        try:
            # Get job ID
            job_id = step.get("job_id", context.get("job_id"))
            if not job_id:
                raise ValueError("No job ID to analyze")

            # Get domains
            domains = step.get("domains", context.get("domains", []))
            if not domains:
                raise ValueError("No domains to analyze")

            # Run analysis
            from ..server.analyzer import MCPAnalyzer
            analyzer = MCPAnalyzer(self.config)
            analysis_id = await analyzer.analyze_results(job_id, domains)

            # Get results
            return {
                "status": "completed",
                "analysis_id": analysis_id,
                "timestamp": datetime.now()
            }

        except Exception as e:
            logger.error(f"Error running analyze step: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now()
            }

    async def _run_fix_step(
        self,
        step: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Run fix step.

        Args:
            step: Step configuration
            context: Pipeline context

        Returns:
            Step results
        """
        try:
            # Get analysis ID
            analysis_id = step.get("analysis_id", context.get("analysis_id"))
            if not analysis_id:
                raise ValueError("No analysis ID to fix")

            # Get domains
            domains = step.get("domains", context.get("domains", []))
            if not domains:
                raise ValueError("No domains to fix")

            # Generate fixes
            from ..server.fixer import MCPFixer
            fixer = MCPFixer(self.config)
            fix_id = await fixer.generate_fixes(analysis_id, domains)

            # Apply fixes
            success = await fixer.apply_fixes(fix_id, domains)

            return {
                "status": "completed" if success else "failed",
                "fix_id": fix_id,
                "timestamp": datetime.now()
            }

        except Exception as e:
            logger.error(f"Error running fix step: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now()
            }

    async def _run_test_step(
        self,
        step: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Run test step.

        Args:
            step: Step configuration
            context: Pipeline context

        Returns:
            Step results
        """
        try:
            # Get test configuration
            test_type = step.get("test_type")
            if not test_type:
                raise ValueError("Missing test type")

            # Run tests
            if test_type == "api":
                results = await self._run_api_tests(step, context)
            elif test_type == "unit":
                results = await self._run_unit_tests(step, context)
            elif test_type == "integration":
                results = await self._run_integration_tests(step, context)
            else:
                raise ValueError(f"Unknown test type: {test_type}")

            return results

        except Exception as e:
            logger.error(f"Error running test step: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now()
            }

    async def _run_deploy_step(
        self,
        step: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Run deploy step.

        Args:
            step: Step configuration
            context: Pipeline context

        Returns:
            Step results
        """
        try:
            # Get deployment configuration
            deploy_type = step.get("deploy_type")
            if not deploy_type:
                raise ValueError("Missing deployment type")

            # Run deployment
            if deploy_type == "kubernetes":
                results = await self._run_kubernetes_deployment(step, context)
            elif deploy_type == "docker":
                results = await self._run_docker_deployment(step, context)
            else:
                raise ValueError(f"Unknown deployment type: {deploy_type}")

            return results

        except Exception as e:
            logger.error(f"Error running deploy step: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now()
            }

    def _update_metrics(self, results: Dict[str, Any]) -> None:
        """Update metrics with pipeline results.

        Args:
            results: Pipeline results
        """
        try:
            # Get metrics
            metrics = self.metrics.get("pipelines", {
                "total": 0,
                "success": 0,
                "failure": 0,
                "stages": {}
            })

            # Update pipeline metrics
            metrics["total"] += 1
            if results["status"] == "completed":
                metrics["success"] += 1
            else:
                metrics["failure"] += 1

            # Update stage metrics
            for stage_name, stage in results.get("stages", {}).items():
                stage_metrics = metrics["stages"].get(stage_name, {
                    "total": 0,
                    "success": 0,
                    "failure": 0
                })
                stage_metrics["total"] += 1
                if stage["status"] == "completed":
                    stage_metrics["success"] += 1
                else:
                    stage_metrics["failure"] += 1
                metrics["stages"][stage_name] = stage_metrics

            # Save metrics
            self.metrics["pipelines"] = metrics

        except Exception as e:
            logger.error(f"Error updating metrics: {e}")

    def get_metrics(self) -> Dict[str, Any]:
        """Get CI/CD metrics.

        Returns:
            Metrics dictionary
        """
        try:
            return {
                "metrics": self.metrics,
                "active_jobs": len(self.active_jobs),
                "timestamp": datetime.now()
            }

        except Exception as e:
            logger.error(f"Error getting metrics: {e}")
            return {}

    def reset_metrics(self) -> None:
        """Reset CI/CD metrics."""
        try:
            self.metrics.clear()

        except Exception as e:
            logger.error(f"Error resetting metrics: {e}")

    def get_health(self) -> Dict[str, Any]:
        """Get CI/CD health.

        Returns:
            Health status dictionary
        """
        try:
            return {
                "status": "healthy" if self.session else "unhealthy",
                "active_jobs": len(self.active_jobs),
                "metrics": self.get_metrics(),
                "timestamp": datetime.now()
            }

        except Exception as e:
            logger.error(f"Error getting health: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now()
            }
