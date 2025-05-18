"""
Enhanced documentation sniffer for documentation quality and completeness checks.
"""
import ast
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from ...core.base.base_sniffer import BaseSniffer
from ...core.utils.result import SniffingResult

logger = logging.getLogger("documentation_sniffer")

class DocumentationSniffer(BaseSniffer):
    """Enhanced sniffer for documentation quality and completeness."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize documentation sniffer.

        Args:
            config: Configuration dictionary for the sniffer
        """
        super().__init__(config)
        self.docstring_checks = self._load_docstring_checks()
        self.readme_checks = self._load_readme_checks()
        self.api_doc_checks = self._load_api_doc_checks()
        self.ai_doc_model = self._load_ai_doc_model()

    def get_sniffer_type(self) -> str:
        """Return the type of this sniffer."""
        return "documentation"

    def _load_docstring_checks(self) -> Dict[str, Dict[str, Any]]:
        """Load docstring check patterns."""
        return {
            "module_docstring": {
                "pattern": r'^"""[\s\S]*?"""',
                "severity": "high",
                "description": "Module-level docstring",
                "fix_template": "Add module-level docstring"
            },
            "class_docstring": {
                "pattern": r'class\s+\w+[^:]*:\s*(?![\s\n]*["\'])',
                "severity": "high",
                "description": "Class-level docstring",
                "fix_template": "Add class-level docstring"
            },
            "function_docstring": {
                "pattern": r'def\s+\w+[^:]*:\s*(?![\s\n]*["\'])',
                "severity": "high",
                "description": "Function-level docstring",
                "fix_template": "Add function-level docstring"
            },
            "args_docstring": {
                "pattern": r'Args:',
                "severity": "medium",
                "description": "Arguments documentation",
                "fix_template": "Document function arguments"
            },
            "returns_docstring": {
                "pattern": r'Returns:',
                "severity": "medium",
                "description": "Return value documentation",
                "fix_template": "Document return value"
            },
            "raises_docstring": {
                "pattern": r'Raises:',
                "severity": "medium",
                "description": "Exceptions documentation",
                "fix_template": "Document raised exceptions"
            }
        }

    def _load_readme_checks(self) -> Dict[str, Dict[str, Any]]:
        """Load README check patterns."""
        return {
            "project_description": {
                "pattern": r'#.*\n[\s\S]*?\n##',
                "severity": "high",
                "description": "Project description",
                "fix_template": "Add project description"
            },
            "installation": {
                "pattern": r'##\s*Installation',
                "severity": "high",
                "description": "Installation instructions",
                "fix_template": "Add installation instructions"
            },
            "usage": {
                "pattern": r'##\s*Usage',
                "severity": "high",
                "description": "Usage instructions",
                "fix_template": "Add usage instructions"
            },
            "examples": {
                "pattern": r'##\s*Examples?',
                "severity": "medium",
                "description": "Code examples",
                "fix_template": "Add code examples"
            },
            "configuration": {
                "pattern": r'##\s*Configuration',
                "severity": "medium",
                "description": "Configuration documentation",
                "fix_template": "Add configuration documentation"
            }
        }

    def _load_api_doc_checks(self) -> Dict[str, Dict[str, Any]]:
        """Load API documentation check patterns."""
        return {
            "endpoint_description": {
                "pattern": r'@(?:app|router)\.(?:get|post|put|delete|patch)\([^)]*\)\s*\n[^"\']',
                "severity": "high",
                "description": "API endpoint description",
                "fix_template": "Add endpoint description"
            },
            "request_params": {
                "pattern": r'@(?:app|router)\.(?:get|post|put|delete|patch)\([^)]*\)\s*\n[^"\']*def[^:]+:\s*(?![\s\n]*["\'].*Parameters:)',
                "severity": "high",
                "description": "Request parameters documentation",
                "fix_template": "Document request parameters"
            },
            "response_format": {
                "pattern": r'@(?:app|router)\.(?:get|post|put|delete|patch)\([^)]*\)\s*\n[^"\']*def[^:]+:\s*(?![\s\n]*["\'].*Returns:)',
                "severity": "high",
                "description": "Response format documentation",
                "fix_template": "Document response format"
            },
            "error_responses": {
                "pattern": r'@(?:app|router)\.(?:get|post|put|delete|patch)\([^)]*\)\s*\n[^"\']*def[^:]+:\s*(?![\s\n]*["\'].*Raises:)',
                "severity": "high",
                "description": "Error responses documentation",
                "fix_template": "Document error responses"
            },
            "authentication": {
                "pattern": r'@(?:login_required|auth\.requires?_auth)[^"\']*def[^:]+:\s*(?![\s\n]*["\'].*Authentication:)',
                "severity": "high",
                "description": "Authentication documentation",
                "fix_template": "Document authentication requirements"
            }
        }

    def _load_ai_doc_model(self) -> Any:
        """Load AI documentation analysis model."""
        try:
            return self.ai_analyzer.load_doc_model()
        except Exception as e:
            logger.error(f"Error loading AI doc model: {e}")
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

            # Run documentation checks
            if file.endswith(".py"):
                await self._check_docstrings(content, result)
                await self._check_api_docs(content, result)
            elif file.lower() == "readme.md":
                await self._check_readme(content, result)

            await self._run_ai_doc_analysis(content, result)

            # Update status
            result.status = not result.has_critical_issues()

            return result

        except Exception as e:
            logger.error(f"Error sniffing file {file}: {e}")
            return SniffingResult(file, self.get_sniffer_type(), status=False)

    async def _check_docstrings(self, content: str, result: SniffingResult) -> None:
        """Check Python docstrings.

        Args:
            content: File content to check
            result: SniffingResult to update
        """
        try:
            # Parse code into AST
            tree = ast.parse(content)

            # Check module docstring
            if not ast.get_docstring(tree):
                result.add_issue({
                    "type": "docstring",
                    "subtype": "module_docstring",
                    "severity": "high",
                    "description": "Missing module docstring",
                    "fix_suggestion": "Add module-level docstring"
                })

            # Check class and function docstrings
            for node in ast.walk(tree):
                if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                    docstring = ast.get_docstring(node)
                    if not docstring:
                        result.add_issue({
                            "type": "docstring",
                            "subtype": f"{node.__class__.__name__.lower()}_docstring",
                            "severity": "high",
                            "description": f"Missing {node.__class__.__name__.lower()} docstring",
                            "line": node.lineno,
                            "name": node.name,
                            "fix_suggestion": f"Add {node.__class__.__name__.lower()}-level docstring"
                        })
                    else:
                        # Check docstring sections
                        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            if node.args.args and "Args:" not in docstring:
                                result.add_issue({
                                    "type": "docstring",
                                    "subtype": "args_docstring",
                                    "severity": "medium",
                                    "description": "Missing Args section",
                                    "line": node.lineno,
                                    "name": node.name,
                                    "fix_suggestion": "Add Args section to docstring"
                                })

                            if "Returns:" not in docstring and not isinstance(node.returns, ast.Constant):
                                result.add_issue({
                                    "type": "docstring",
                                    "subtype": "returns_docstring",
                                    "severity": "medium",
                                    "description": "Missing Returns section",
                                    "line": node.lineno,
                                    "name": node.name,
                                    "fix_suggestion": "Add Returns section to docstring"
                                })

            # Run AI docstring analysis
            if self.ai_doc_model:
                ai_issues = await self.ai_analyzer.check_docstrings(
                    content,
                    self.ai_doc_model
                )
                for issue in ai_issues:
                    result.add_issue(issue)

        except Exception as e:
            logger.error(f"Error checking docstrings: {e}")

    async def _check_readme(self, content: str, result: SniffingResult) -> None:
        """Check README documentation.

        Args:
            content: File content to check
            result: SniffingResult to update
        """
        try:
            for check_type, check_info in self.readme_checks.items():
                matches = re.finditer(check_info["pattern"], content, re.MULTILINE)
                if not list(matches):
                    result.add_issue({
                        "type": "readme",
                        "subtype": check_type,
                        "severity": check_info["severity"],
                        "description": f"Missing {check_info['description']}",
                        "fix_suggestion": check_info["fix_template"]
                    })

            # Check section content
            sections = re.split(r'##\s+', content)[1:]
            for section in sections:
                # Get section name and content
                section_name = section.split("\n")[0].strip()
                section_content = "\n".join(section.split("\n")[1:]).strip()

                # Check content length
                if len(section_content) < 50:  # Minimum content length
                    result.add_issue({
                        "type": "readme",
                        "subtype": "section_content",
                        "severity": "medium",
                        "description": f"Insufficient content in section: {section_name}",
                        "section": section_name,
                        "fix_suggestion": f"Add more content to {section_name} section"
                    })

            # Run AI README analysis
            if self.ai_doc_model:
                ai_issues = await self.ai_analyzer.check_readme(
                    content,
                    self.ai_doc_model
                )
                for issue in ai_issues:
                    result.add_issue(issue)

        except Exception as e:
            logger.error(f"Error checking README: {e}")

    async def _check_api_docs(self, content: str, result: SniffingResult) -> None:
        """Check API documentation.

        Args:
            content: File content to check
            result: SniffingResult to update
        """
        try:
            for check_type, check_info in self.api_doc_checks.items():
                matches = re.finditer(check_info["pattern"], content, re.MULTILINE)
                for match in matches:
                    result.add_issue({
                        "type": "api_doc",
                        "subtype": check_type,
                        "severity": check_info["severity"],
                        "description": f"Missing {check_info['description']}",
                        "line": content.count("\n", 0, match.start()) + 1,
                        "code": match.group(0).strip(),
                        "fix_suggestion": check_info["fix_template"]
                    })

            # Run AI API doc analysis
            if self.ai_doc_model:
                ai_issues = await self.ai_analyzer.check_api_docs(
                    content,
                    self.ai_doc_model
                )
                for issue in ai_issues:
                    result.add_issue(issue)

        except Exception as e:
            logger.error(f"Error checking API docs: {e}")

    async def _run_ai_doc_analysis(self, content: str, result: SniffingResult) -> None:
        """Run AI-powered documentation analysis.

        Args:
            content: File content to analyze
            result: SniffingResult to update
        """
        try:
            if self.ai_doc_model:
                # Run comprehensive AI analysis
                analysis = await self.ai_analyzer.analyze_documentation(
                    content,
                    self.ai_doc_model
                )

                # Add issues from AI analysis
                for issue in analysis.get("issues", []):
                    result.add_issue(issue)

                # Update metrics
                result.update_metrics({
                    "ai_doc_analysis": {
                        "completeness_score": analysis.get("completeness_score", 0.0),
                        "quality_score": analysis.get("quality_score", 0.0),
                        "clarity_score": analysis.get("clarity_score", 0.0)
                    }
                })

        except Exception as e:
            logger.error(f"Error running AI doc analysis: {e}")

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

            # Run documentation checks on updated content
            if suggestion["file"].endswith(".py"):
                await self._check_docstrings(content, result)
                await self._check_api_docs(content, result)
            elif suggestion["file"].lower() == "readme.md":
                await self._check_readme(content, result)

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
