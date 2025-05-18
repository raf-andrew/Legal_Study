"""
Enhanced browser sniffer for cross-browser testing, accessibility checks, and performance monitoring.
"""
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from ...core.base.base_sniffer import BaseSniffer
from ...core.utils.result import SniffingResult

logger = logging.getLogger("browser_sniffer")

class BrowserSniffer(BaseSniffer):
    """Enhanced sniffer for browser compatibility and accessibility testing."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize browser sniffer.

        Args:
            config: Configuration dictionary for the sniffer
        """
        super().__init__(config)
        self.browser_checks = self._load_browser_checks()
        self.accessibility_checks = self._load_accessibility_checks()
        self.performance_checks = self._load_performance_checks()
        self.ai_browser_model = self._load_ai_browser_model()

    def get_sniffer_type(self) -> str:
        """Return the type of this sniffer."""
        return "browser"

    def _load_browser_checks(self) -> Dict[str, Dict[str, Any]]:
        """Load browser compatibility check patterns."""
        return {
            "vendor_prefixes": {
                "pattern": r"-webkit-|-moz-|-ms-|-o-",
                "severity": "medium",
                "description": "Vendor-specific prefixes found",
                "fix_template": "Consider using autoprefixer or standard properties"
            },
            "deprecated_features": {
                "pattern": r"document\.write|document\.all|document\.layers",
                "severity": "high",
                "description": "Use of deprecated browser features",
                "fix_template": "Use modern alternatives"
            },
            "browser_specific": {
                "pattern": r"\.innerText|\.outerHTML|\.attachEvent",
                "severity": "medium",
                "description": "Browser-specific features detected",
                "fix_template": "Use cross-browser alternatives"
            },
            "ie_hacks": {
                "pattern": r"<!--\[if|<!\[endif\]-->|_:-ms-|@media screen\sand\s\(-ms-high-contrast",
                "severity": "medium",
                "description": "Internet Explorer specific hacks found",
                "fix_template": "Use modern cross-browser approaches"
            },
            "mobile_meta": {
                "pattern": r'<meta\s+name=["\']viewport["\']',
                "severity": "high",
                "description": "Missing mobile viewport meta tag",
                "fix_template": "Add viewport meta tag for mobile responsiveness"
            }
        }

    def _load_accessibility_checks(self) -> Dict[str, Dict[str, Any]]:
        """Load accessibility check patterns."""
        return {
            "alt_text": {
                "pattern": r'<img[^>]+(?!alt=)[^>]*>|<img[^>]+alt=["\']["\'][^>]*>',
                "severity": "high",
                "description": "Missing or empty alt text",
                "wcag": "1.1.1",
                "fix_template": "Add descriptive alt text to images"
            },
            "aria_labels": {
                "pattern": r'<(?:button|a|input|select|textarea)[^>]+(?!aria-label=|aria-labelledby=)[^>]*>',
                "severity": "high",
                "description": "Missing ARIA labels",
                "wcag": "4.1.2",
                "fix_template": "Add appropriate ARIA labels"
            },
            "heading_structure": {
                "pattern": r'<h[1-6][^>]*>.*?</h[1-6]>',
                "severity": "medium",
                "description": "Check heading structure",
                "wcag": "1.3.1",
                "fix_template": "Ensure proper heading hierarchy"
            },
            "color_contrast": {
                "pattern": r'color:|background-color:|background:',
                "severity": "high",
                "description": "Verify color contrast ratios",
                "wcag": "1.4.3",
                "fix_template": "Ensure sufficient color contrast"
            },
            "keyboard_nav": {
                "pattern": r'tabindex="-1"|onkeydown=|onkeypress=|onkeyup=',
                "severity": "high",
                "description": "Check keyboard navigation",
                "wcag": "2.1.1",
                "fix_template": "Ensure proper keyboard navigation"
            }
        }

    def _load_performance_checks(self) -> Dict[str, Dict[str, Any]]:
        """Load performance check patterns."""
        return {
            "large_images": {
                "pattern": r'<img[^>]+src=["\'][^"\']+\.(jpg|jpeg|png|gif)["\'][^>]*>',
                "severity": "medium",
                "description": "Check image sizes and optimization",
                "fix_template": "Optimize images and use appropriate formats"
            },
            "render_blocking": {
                "pattern": r'<link[^>]+rel=["\']stylesheet["\'][^>]*>(?!.*media=["\']print["\'])|<script[^>]*>(?!.*async|.*defer)',
                "severity": "high",
                "description": "Render-blocking resources found",
                "fix_template": "Use async/defer for scripts and optimize CSS loading"
            },
            "heavy_animations": {
                "pattern": r'@keyframes|animation:|transition:',
                "severity": "medium",
                "description": "Check animation performance",
                "fix_template": "Optimize animations for performance"
            },
            "resource_hints": {
                "pattern": r'<link[^>]+rel=["\'](?:preload|prefetch|preconnect)["\'][^>]*>',
                "severity": "low",
                "description": "Consider using resource hints",
                "fix_template": "Add appropriate resource hints"
            }
        }

    def _load_ai_browser_model(self) -> Any:
        """Load AI browser analysis model."""
        try:
            return self.ai_analyzer.load_browser_model()
        except Exception as e:
            logger.error(f"Error loading AI browser model: {e}")
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

            # Run browser checks
            await self._check_browser_compatibility(content, result)
            await self._check_accessibility(content, result)
            await self._check_performance(content, result)
            await self._run_ai_browser_analysis(content, result)

            # Update status
            result.status = not result.has_critical_issues()

            return result

        except Exception as e:
            logger.error(f"Error sniffing file {file}: {e}")
            return SniffingResult(file, self.get_sniffer_type(), status=False)

    async def _check_browser_compatibility(self, content: str, result: SniffingResult) -> None:
        """Check for browser compatibility issues.

        Args:
            content: File content to check
            result: SniffingResult to update
        """
        try:
            for check_type, check_info in self.browser_checks.items():
                matches = re.finditer(check_info["pattern"], content, re.MULTILINE)
                for match in matches:
                    issue = {
                        "type": "browser_compatibility",
                        "subtype": check_type,
                        "severity": check_info["severity"],
                        "description": check_info["description"],
                        "line": content.count("\n", 0, match.start()) + 1,
                        "code": match.group(0).strip(),
                        "fix_suggestion": check_info["fix_template"]
                    }
                    result.add_issue(issue)

            # Run AI browser compatibility checks
            if self.ai_browser_model:
                ai_issues = await self.ai_analyzer.check_browser_compatibility(
                    content,
                    self.ai_browser_model
                )
                for issue in ai_issues:
                    result.add_issue(issue)

        except Exception as e:
            logger.error(f"Error checking browser compatibility: {e}")

    async def _check_accessibility(self, content: str, result: SniffingResult) -> None:
        """Check for accessibility issues.

        Args:
            content: File content to check
            result: SniffingResult to update
        """
        try:
            for check_type, check_info in self.accessibility_checks.items():
                matches = re.finditer(check_info["pattern"], content, re.MULTILINE)
                for match in matches:
                    issue = {
                        "type": "accessibility",
                        "subtype": check_type,
                        "severity": check_info["severity"],
                        "description": check_info["description"],
                        "line": content.count("\n", 0, match.start()) + 1,
                        "code": match.group(0).strip(),
                        "wcag": check_info["wcag"],
                        "fix_suggestion": check_info["fix_template"]
                    }
                    result.add_issue(issue)

            # Run AI accessibility checks
            if self.ai_browser_model:
                ai_issues = await self.ai_analyzer.check_accessibility(
                    content,
                    self.ai_browser_model
                )
                for issue in ai_issues:
                    result.add_issue(issue)

        except Exception as e:
            logger.error(f"Error checking accessibility: {e}")

    async def _check_performance(self, content: str, result: SniffingResult) -> None:
        """Check for performance issues.

        Args:
            content: File content to check
            result: SniffingResult to update
        """
        try:
            for check_type, check_info in self.performance_checks.items():
                matches = re.finditer(check_info["pattern"], content, re.MULTILINE)
                for match in matches:
                    issue = {
                        "type": "performance",
                        "subtype": check_type,
                        "severity": check_info["severity"],
                        "description": check_info["description"],
                        "line": content.count("\n", 0, match.start()) + 1,
                        "code": match.group(0).strip(),
                        "fix_suggestion": check_info["fix_template"]
                    }
                    result.add_issue(issue)

            # Run AI performance checks
            if self.ai_browser_model:
                ai_issues = await self.ai_analyzer.check_performance(
                    content,
                    self.ai_browser_model
                )
                for issue in ai_issues:
                    result.add_issue(issue)

        except Exception as e:
            logger.error(f"Error checking performance: {e}")

    async def _run_ai_browser_analysis(self, content: str, result: SniffingResult) -> None:
        """Run AI-powered browser analysis.

        Args:
            content: File content to analyze
            result: SniffingResult to update
        """
        try:
            if self.ai_browser_model:
                # Run comprehensive AI analysis
                analysis = await self.ai_analyzer.analyze_browser(
                    content,
                    self.ai_browser_model
                )

                # Add issues from AI analysis
                for issue in analysis.get("issues", []):
                    result.add_issue(issue)

                # Update metrics
                result.update_metrics({
                    "ai_browser_analysis": {
                        "compatibility_score": analysis.get("compatibility_score", 0.0),
                        "accessibility_score": analysis.get("accessibility_score", 0.0),
                        "performance_score": analysis.get("performance_score", 0.0)
                    }
                })

        except Exception as e:
            logger.error(f"Error running AI browser analysis: {e}")

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

            # Run browser checks on updated content
            await self._check_browser_compatibility(content, result)
            await self._check_accessibility(content, result)
            await self._check_performance(content, result)

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
