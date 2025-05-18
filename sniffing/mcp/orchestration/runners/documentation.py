"""
Documentation runner for documentation quality and completeness checks.
"""
import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

from .base import BaseRunner
from ...server.config import ServerConfig

logger = logging.getLogger("documentation_runner")

class DocumentationRunner(BaseRunner):
    """Runner for documentation testing."""

    def __init__(self, config: ServerConfig):
        """Initialize documentation runner.

        Args:
            config: Server configuration
        """
        super().__init__("documentation", config)
        self.doc_patterns = self._load_doc_patterns()
        self.style_rules = self._load_style_rules()
        self.completeness_rules = self._load_completeness_rules()

    def _load_doc_patterns(self) -> Dict[str, Any]:
        """Load documentation patterns.

        Returns:
            Dictionary of documentation patterns
        """
        try:
            patterns = self.runner_config.get("doc_patterns", {})
            if not patterns:
                logger.warning("No documentation patterns configured")
            return patterns

        except Exception as e:
            logger.error(f"Error loading documentation patterns: {e}")
            return {}

    def _load_style_rules(self) -> Dict[str, Any]:
        """Load style rules.

        Returns:
            Dictionary of style rules
        """
        try:
            rules = self.runner_config.get("style_rules", {})
            if not rules:
                logger.warning("No style rules configured")
            return rules

        except Exception as e:
            logger.error(f"Error loading style rules: {e}")
            return {}

    def _load_completeness_rules(self) -> Dict[str, Any]:
        """Load completeness rules.

        Returns:
            Dictionary of completeness rules
        """
        try:
            rules = self.runner_config.get("completeness_rules", {})
            if not rules:
                logger.warning("No completeness rules configured")
            return rules

        except Exception as e:
            logger.error(f"Error loading completeness rules: {e}")
            return {}

    async def _run_tests(self, files: List[str]) -> Dict[str, Any]:
        """Run documentation tests.

        Args:
            files: Files to test

        Returns:
            Test results
        """
        try:
            results = {
                "status": "running",
                "timestamp": datetime.now(),
                "files": files,
                "issues": [],
                "coverage": {}
            }

            # Check documentation
            doc_results = await self._check_documentation(files)
            results["documentation"] = doc_results

            # Check style
            style_results = await self._check_style(files)
            results["style"] = style_results

            # Check completeness
            completeness_results = await self._check_completeness(files)
            results["completeness"] = completeness_results

            # Calculate coverage
            coverage = await self._calculate_documentation_coverage(
                files,
                doc_results,
                style_results,
                completeness_results
            )
            results["coverage"] = coverage

            # Aggregate issues
            issues = []
            issues.extend(doc_results.get("issues", []))
            issues.extend(style_results.get("issues", []))
            issues.extend(completeness_results.get("issues", []))
            results["issues"] = issues

            # Update status
            results["status"] = "completed"

            return results

        except Exception as e:
            logger.error(f"Error running documentation tests: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now()
            }

    async def _check_documentation(
        self,
        files: List[str]
    ) -> Dict[str, Any]:
        """Check documentation quality.

        Args:
            files: Files to check

        Returns:
            Documentation check results
        """
        try:
            results = {
                "status": "running",
                "timestamp": datetime.now(),
                "files": files,
                "issues": []
            }

            for file in files:
                # Check file documentation
                file_results = await self._check_file_documentation(file)
                results["issues"].extend(file_results.get("issues", []))

            # Update status
            results["status"] = "completed"

            return results

        except Exception as e:
            logger.error(f"Error checking documentation: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now()
            }

    async def _check_file_documentation(
        self,
        file: str
    ) -> Dict[str, Any]:
        """Check file documentation.

        Args:
            file: File to check

        Returns:
            File documentation results
        """
        try:
            results = {
                "file": file,
                "issues": []
            }

            # Read file content
            with open(file, "r") as f:
                content = f.read()

            # Parse AST
            import ast
            tree = ast.parse(content)

            # Check each pattern
            for pattern_id, pattern in self.doc_patterns.items():
                matches = await self._check_doc_pattern(
                    tree,
                    pattern
                )
                if matches:
                    results["issues"].extend([
                        {
                            "id": f"DOC-{pattern_id}-{i}",
                            "type": "documentation",
                            "pattern": pattern_id,
                            "severity": pattern.get("severity", "medium"),
                            "description": pattern.get("description", ""),
                            "node": match.get("node"),
                            "fix": pattern.get("fix", "")
                        }
                        for i, match in enumerate(matches)
                    ])

            return results

        except Exception as e:
            logger.error(f"Error checking file {file}: {e}")
            return {
                "file": file,
                "error": str(e)
            }

    async def _check_doc_pattern(
        self,
        tree: Any,
        pattern: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Check AST for documentation pattern.

        Args:
            tree: AST to check
            pattern: Pattern to check for

        Returns:
            List of pattern matches
        """
        try:
            matches = []

            class DocVisitor(ast.NodeVisitor):
                def __init__(self, pattern):
                    self.pattern = pattern
                    self.matches = []

                def visit_FunctionDef(self, node):
                    if not ast.get_docstring(node):
                        self.matches.append({
                            "node": node,
                            "type": "function",
                            "name": node.name
                        })
                    self.generic_visit(node)

                def visit_ClassDef(self, node):
                    if not ast.get_docstring(node):
                        self.matches.append({
                            "node": node,
                            "type": "class",
                            "name": node.name
                        })
                    self.generic_visit(node)

                def visit_Module(self, node):
                    if not ast.get_docstring(node):
                        self.matches.append({
                            "node": node,
                            "type": "module"
                        })
                    self.generic_visit(node)

            visitor = DocVisitor(pattern)
            visitor.visit(tree)
            return visitor.matches

        except Exception as e:
            logger.error(f"Error checking pattern: {e}")
            return []

    async def _check_style(
        self,
        files: List[str]
    ) -> Dict[str, Any]:
        """Check documentation style.

        Args:
            files: Files to check

        Returns:
            Style check results
        """
        try:
            results = {
                "status": "running",
                "timestamp": datetime.now(),
                "files": files,
                "issues": []
            }

            for file in files:
                # Check file style
                file_results = await self._check_file_style(file)
                results["issues"].extend(file_results.get("issues", []))

            # Update status
            results["status"] = "completed"

            return results

        except Exception as e:
            logger.error(f"Error checking style: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now()
            }

    async def _check_file_style(
        self,
        file: str
    ) -> Dict[str, Any]:
        """Check file documentation style.

        Args:
            file: File to check

        Returns:
            File style results
        """
        try:
            results = {
                "file": file,
                "issues": []
            }

            # Read file content
            with open(file, "r") as f:
                content = f.read()

            # Check each rule
            for rule_id, rule in self.style_rules.items():
                violations = await self._check_style_rule(
                    content,
                    rule
                )
                if violations:
                    results["issues"].extend([
                        {
                            "id": f"STY-{rule_id}-{i}",
                            "type": "style",
                            "rule": rule_id,
                            "severity": rule.get("severity", "medium"),
                            "description": rule.get("description", ""),
                            "line": violation.get("line"),
                            "text": violation.get("text"),
                            "fix": rule.get("fix", "")
                        }
                        for i, violation in enumerate(violations)
                    ])

            return results

        except Exception as e:
            logger.error(f"Error checking file {file}: {e}")
            return {
                "file": file,
                "error": str(e)
            }

    async def _check_style_rule(
        self,
        content: str,
        rule: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Check content for style rule.

        Args:
            content: Content to check
            rule: Rule to check for

        Returns:
            List of rule violations
        """
        try:
            violations = []
            lines = content.split("\n")

            for i, line in enumerate(lines):
                if rule.get("regex"):
                    # Use regex pattern
                    import re
                    if re.search(rule["regex"], line):
                        violations.append({
                            "line": i + 1,
                            "text": line.strip()
                        })

            return violations

        except Exception as e:
            logger.error(f"Error checking rule: {e}")
            return []

    async def _check_completeness(
        self,
        files: List[str]
    ) -> Dict[str, Any]:
        """Check documentation completeness.

        Args:
            files: Files to check

        Returns:
            Completeness check results
        """
        try:
            results = {
                "status": "running",
                "timestamp": datetime.now(),
                "files": files,
                "issues": []
            }

            for file in files:
                # Check file completeness
                file_results = await self._check_file_completeness(file)
                results["issues"].extend(file_results.get("issues", []))

            # Update status
            results["status"] = "completed"

            return results

        except Exception as e:
            logger.error(f"Error checking completeness: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now()
            }

    async def _check_file_completeness(
        self,
        file: str
    ) -> Dict[str, Any]:
        """Check file documentation completeness.

        Args:
            file: File to check

        Returns:
            File completeness results
        """
        try:
            results = {
                "file": file,
                "issues": []
            }

            # Read file content
            with open(file, "r") as f:
                content = f.read()

            # Parse AST
            import ast
            tree = ast.parse(content)

            # Check each rule
            for rule_id, rule in self.completeness_rules.items():
                violations = await self._check_completeness_rule(
                    tree,
                    rule
                )
                if violations:
                    results["issues"].extend([
                        {
                            "id": f"CMP-{rule_id}-{i}",
                            "type": "completeness",
                            "rule": rule_id,
                            "severity": rule.get("severity", "medium"),
                            "description": rule.get("description", ""),
                            "node": violation.get("node"),
                            "missing": violation.get("missing"),
                            "fix": rule.get("fix", "")
                        }
                        for i, violation in enumerate(violations)
                    ])

            return results

        except Exception as e:
            logger.error(f"Error checking file {file}: {e}")
            return {
                "file": file,
                "error": str(e)
            }

    async def _check_completeness_rule(
        self,
        tree: Any,
        rule: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Check AST for completeness rule.

        Args:
            tree: AST to check
            rule: Rule to check for

        Returns:
            List of rule violations
        """
        try:
            violations = []

            class CompletenessVisitor(ast.NodeVisitor):
                def __init__(self, rule):
                    self.rule = rule
                    self.violations = []

                def visit_FunctionDef(self, node):
                    docstring = ast.get_docstring(node)
                    if docstring:
                        # Check required sections
                        missing = []
                        for section in self.rule.get("required_sections", []):
                            if section not in docstring:
                                missing.append(section)
                        if missing:
                            self.violations.append({
                                "node": node,
                                "type": "function",
                                "name": node.name,
                                "missing": missing
                            })
                    self.generic_visit(node)

                def visit_ClassDef(self, node):
                    docstring = ast.get_docstring(node)
                    if docstring:
                        # Check required sections
                        missing = []
                        for section in self.rule.get("required_sections", []):
                            if section not in docstring:
                                missing.append(section)
                        if missing:
                            self.violations.append({
                                "node": node,
                                "type": "class",
                                "name": node.name,
                                "missing": missing
                            })
                    self.generic_visit(node)

            visitor = CompletenessVisitor(rule)
            visitor.visit(tree)
            return visitor.violations

        except Exception as e:
            logger.error(f"Error checking rule: {e}")
            return []

    async def _calculate_documentation_coverage(
        self,
        files: List[str],
        doc_results: Dict[str, Any],
        style_results: Dict[str, Any],
        completeness_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate documentation coverage.

        Args:
            files: Files tested
            doc_results: Documentation check results
            style_results: Style check results
            completeness_results: Completeness check results

        Returns:
            Coverage metrics
        """
        try:
            # Count total elements
            total_elements = 0
            documented_elements = 0

            for file in files:
                # Parse AST
                with open(file, "r") as f:
                    content = f.read()
                    import ast
                    tree = ast.parse(content)

                # Count elements
                class ElementCounter(ast.NodeVisitor):
                    def __init__(self):
                        self.total = 0
                        self.documented = 0

                    def visit_FunctionDef(self, node):
                        self.total += 1
                        if ast.get_docstring(node):
                            self.documented += 1
                        self.generic_visit(node)

                    def visit_ClassDef(self, node):
                        self.total += 1
                        if ast.get_docstring(node):
                            self.documented += 1
                        self.generic_visit(node)

                    def visit_Module(self, node):
                        self.total += 1
                        if ast.get_docstring(node):
                            self.documented += 1
                        self.generic_visit(node)

                counter = ElementCounter()
                counter.visit(tree)
                total_elements += counter.total
                documented_elements += counter.documented

            return {
                "total_elements": total_elements,
                "documented_elements": documented_elements,
                "coverage_percent": (
                    documented_elements / total_elements * 100
                    if total_elements > 0 else 0
                ),
                "style_violations": len(style_results.get("issues", [])),
                "completeness_violations": len(completeness_results.get("issues", []))
            }

        except Exception as e:
            logger.error(f"Error calculating coverage: {e}")
            return {
                "total_elements": 0,
                "documented_elements": 0,
                "coverage_percent": 0,
                "style_violations": 0,
                "completeness_violations": 0
            }
