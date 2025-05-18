"""
Enhanced functional sniffer for API testing, integration checks, and error handling analysis.
"""
import asyncio
import ast
import inspect
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from ...core.base.base_sniffer import BaseSniffer
from ...core.utils.result import SniffingResult

logger = logging.getLogger("functional_sniffer")

class FunctionalSniffer(BaseSniffer):
    """Enhanced sniffer for functional testing and API validation."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize functional sniffer.

        Args:
            config: Configuration dictionary for the sniffer
        """
        super().__init__(config)
        self.api_checks = self._load_api_checks()
        self.integration_checks = self._load_integration_checks()
        self.error_checks = self._load_error_checks()
        self.ai_functional_model = self._load_ai_functional_model()

    def get_sniffer_type(self) -> str:
        """Return the type of this sniffer."""
        return "functional"

    def _load_api_checks(self) -> Dict[str, Dict[str, Any]]:
        """Load API check patterns."""
        return {
            "endpoint_definition": {
                "pattern": r"@(?:app|router)\.(?:get|post|put|delete|patch)\(['\"]([^'\"]+)['\"]",
                "severity": "high",
                "description": "API endpoint definition",
                "fix_template": "Add proper endpoint documentation and validation"
            },
            "request_validation": {
                "pattern": r"request\.(json|form|args|params)",
                "severity": "high",
                "description": "Request data validation",
                "fix_template": "Add request data validation"
            },
            "response_format": {
                "pattern": r"return\s+(?:jsonify\(.*\)|json\.dumps\(.*\))",
                "severity": "medium",
                "description": "API response format",
                "fix_template": "Standardize API response format"
            },
            "authentication": {
                "pattern": r"@(?:login_required|auth\.requires?_auth)",
                "severity": "critical",
                "description": "Authentication check",
                "fix_template": "Add proper authentication"
            },
            "rate_limiting": {
                "pattern": r"@limiter\.limit",
                "severity": "medium",
                "description": "Rate limiting",
                "fix_template": "Add rate limiting"
            }
        }

    def _load_integration_checks(self) -> Dict[str, Dict[str, Any]]:
        """Load integration check patterns."""
        return {
            "database": {
                "pattern": r"(?:session|db)\.(query|execute|commit|rollback)",
                "severity": "high",
                "description": "Database integration",
                "fix_template": "Add proper database error handling and transactions"
            },
            "external_api": {
                "pattern": r"requests?\.(get|post|put|delete|patch)",
                "severity": "high",
                "description": "External API integration",
                "fix_template": "Add proper error handling and retries"
            },
            "cache": {
                "pattern": r"cache\.(get|set|delete)",
                "severity": "medium",
                "description": "Cache integration",
                "fix_template": "Add cache error handling"
            },
            "queue": {
                "pattern": r"(?:queue|broker)\.(publish|send|push)",
                "severity": "high",
                "description": "Message queue integration",
                "fix_template": "Add queue error handling"
            },
            "file_system": {
                "pattern": r"(?:open|read|write|close)\(['\"].*['\"]",
                "severity": "medium",
                "description": "File system integration",
                "fix_template": "Add proper file handling"
            }
        }

    def _load_error_checks(self) -> Dict[str, Dict[str, Any]]:
        """Load error handling check patterns."""
        return {
            "exception_handling": {
                "pattern": r"try:.*?except\s+(?:\w+\s+)?as\s+\w+:",
                "severity": "high",
                "description": "Exception handling",
                "fix_template": "Add proper exception handling"
            },
            "error_logging": {
                "pattern": r"logger\.(error|exception|critical)",
                "severity": "high",
                "description": "Error logging",
                "fix_template": "Add proper error logging"
            },
            "error_response": {
                "pattern": r"return\s+jsonify\(\{['\"]error['\"]:.*\}\)",
                "severity": "medium",
                "description": "Error response format",
                "fix_template": "Standardize error response format"
            },
            "validation": {
                "pattern": r"validate|schema\.load|form\.validate",
                "severity": "high",
                "description": "Data validation",
                "fix_template": "Add proper data validation"
            },
            "cleanup": {
                "pattern": r"finally:",
                "severity": "medium",
                "description": "Resource cleanup",
                "fix_template": "Add proper resource cleanup"
            }
        }

    def _load_ai_functional_model(self) -> Any:
        """Load AI functional analysis model."""
        try:
            return self.ai_analyzer.load_functional_model()
        except Exception as e:
            logger.error(f"Error loading AI functional model: {e}")
            return None

    async def _sniff_file_impl(self, file: str) -> SniffingResult:
        """Implementation of file sniffing logic.

        Args:
            file: Path to the file to sniff.

        Returns:
            SniffingResult object
        """
        try:
            # Create result
            result = SniffingResult(file, self.get_sniffer_type())

            # Read file content
            with open(file, "r") as f:
                content = f.read()

            # Run functional checks
            await self._check_api(content, result)
            await self._check_integration(content, result)
            await self._check_error_handling(content, result)
            await self._run_ai_functional_analysis(content, result)

            # Update status
            result.status = not result.has_critical_issues()

            return result

        except Exception as e:
            logger.error(f"Error sniffing file {file}: {e}")
            return SniffingResult(file, self.get_sniffer_type(), status=False)

    async def _check_api(self, content: str, result: SniffingResult) -> None:
        """Check for API issues.

        Args:
            content: File content to check
            result: SniffingResult to update
        """
        try:
            for check_type, check_info in self.api_checks.items():
                matches = re.finditer(check_info["pattern"], content, re.MULTILINE)
                for match in matches:
                    issue = {
                        "type": "api",
                        "subtype": check_type,
                        "severity": check_info["severity"],
                        "description": check_info["description"],
                        "line": content.count("\n", 0, match.start()) + 1,
                        "code": match.group(0).strip(),
                        "fix_suggestion": check_info["fix_template"]
                    }
                    result.add_issue(issue)

            # Run AI API checks
            if self.ai_functional_model:
                ai_issues = await self.ai_analyzer.check_api(
                    content,
                    self.ai_functional_model
                )
                for issue in ai_issues:
                    result.add_issue(issue)

        except Exception as e:
            logger.error(f"Error checking API: {e}")

    async def _check_integration(self, content: str, result: SniffingResult) -> None:
        """Check for integration issues.

        Args:
            content: File content to check
            result: SniffingResult to update
        """
        try:
            for check_type, check_info in self.integration_checks.items():
                matches = re.finditer(check_info["pattern"], content, re.MULTILINE)
                for match in matches:
                    issue = {
                        "type": "integration",
                        "subtype": check_type,
                        "severity": check_info["severity"],
                        "description": check_info["description"],
                        "line": content.count("\n", 0, match.start()) + 1,
                        "code": match.group(0).strip(),
                        "fix_suggestion": check_info["fix_template"]
                    }
                    result.add_issue(issue)

            # Run AI integration checks
            if self.ai_functional_model:
                ai_issues = await self.ai_analyzer.check_integration(
                    content,
                    self.ai_functional_model
                )
                for issue in ai_issues:
                    result.add_issue(issue)

        except Exception as e:
            logger.error(f"Error checking integration: {e}")

    async def _check_error_handling(self, content: str, result: SniffingResult) -> None:
        """Check for error handling issues.

        Args:
            content: File content to check
            result: SniffingResult to update
        """
        try:
            for check_type, check_info in self.error_checks.items():
                matches = re.finditer(check_info["pattern"], content, re.MULTILINE)
                for match in matches:
                    issue = {
                        "type": "error_handling",
                        "subtype": check_type,
                        "severity": check_info["severity"],
                        "description": check_info["description"],
                        "line": content.count("\n", 0, match.start()) + 1,
                        "code": match.group(0).strip(),
                        "fix_suggestion": check_info["fix_template"]
                    }
                    result.add_issue(issue)

            # Run AI error handling checks
            if self.ai_functional_model:
                ai_issues = await self.ai_analyzer.check_error_handling(
                    content,
                    self.ai_functional_model
                )
                for issue in ai_issues:
                    result.add_issue(issue)

        except Exception as e:
            logger.error(f"Error checking error handling: {e}")

    async def _run_ai_functional_analysis(self, content: str, result: SniffingResult) -> None:
        """Run AI-powered functional analysis.

        Args:
            content: File content to analyze
            result: SniffingResult to update
        """
        try:
            if self.ai_functional_model:
                # Run comprehensive AI analysis
                analysis = await self.ai_analyzer.analyze_functional(
                    content,
                    self.ai_functional_model
                )

                # Add issues from AI analysis
                for issue in analysis.get("issues", []):
                    result.add_issue(issue)

                # Update metrics
                result.update_metrics({
                    "ai_functional_analysis": {
                        "api_score": analysis.get("api_score", 0.0),
                        "integration_score": analysis.get("integration_score", 0.0),
                        "error_handling_score": analysis.get("error_handling_score", 0.0)
                    }
                })

        except Exception as e:
            logger.error(f"Error running AI functional analysis: {e}")

    async def _apply_fixes(self, suggestions: List[Dict[str, Any]]) -> bool:
        """Apply fix suggestions to issues.

        Args:
            suggestions: List of fix suggestions from AI

        Returns:
            True if all fixes were applied successfully, False otherwise
        """
        try:
            success = True
            for suggestion in suggestions:
                # Get file content
                with open(suggestion["file"], "r") as f:
                    content = f.read()

                # Apply fix
                if suggestion.get("fix_type") == "replace":
                    content = content.replace(
                        suggestion["old_code"],
                        suggestion["new_code"]
                    )
                elif suggestion.get("fix_type") == "insert":
                    lines = content.splitlines()
                    lines.insert(
                        suggestion["line"] - 1,
                        suggestion["code"]
                    )
                    content = "\n".join(lines)
                else:
                    logger.warning(f"Unknown fix type: {suggestion.get('fix_type')}")
                    success = False
                    continue

                # Write fixed content
                with open(suggestion["file"], "w") as f:
                    f.write(content)

                # Validate fix
                if not await self._validate_fix(suggestion, content):
                    success = False

            return success

        except Exception as e:
            logger.error(f"Error applying fixes: {e}")
            return False

    async def _validate_fix(self, suggestion: Dict[str, Any], content: str) -> bool:
        """Validate that a fix was successful.

        Args:
            suggestion: Fix suggestion that was applied
            content: Updated file content

        Returns:
            True if fix was successful, False otherwise
        """
        try:
            # Create temporary result
            result = SniffingResult(suggestion["file"], self.get_sniffer_type())

            # Run functional checks on updated content
            await self._check_api(content, result)
            await self._check_integration(content, result)
            await self._check_error_handling(content, result)

            # Check if original issue was fixed
            for issue in result.issues:
                if (
                    issue["type"] == suggestion.get("issue_type") and
                    issue["subtype"] == suggestion.get("issue_subtype")
                ):
                    return False

            return True

        except Exception as e:
            logger.error(f"Error validating fix: {e}")
            return False
