"""
Git integration for sniffing operations.
"""
import asyncio
import logging
import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from git import Repo
from git.exc import GitCommandError

logger = logging.getLogger("git_integration")

class GitIntegration:
    """Git integration for sniffing operations."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.repo_path = Path(config.get("repo_path", "."))
        self.hooks_path = self.repo_path / ".git" / "hooks"
        self.repo = Repo(self.repo_path)
        self._setup_hooks()

    def _setup_hooks(self) -> None:
        """Set up Git hooks."""
        try:
            # Create hooks directory
            self.hooks_path.mkdir(parents=True, exist_ok=True)

            # Install hooks
            hooks = {
                "pre-commit": self._pre_commit_hook,
                "pre-push": self._pre_push_hook,
                "post-commit": self._post_commit_hook,
                "post-merge": self._post_merge_hook
            }

            for hook_name, hook_func in hooks.items():
                hook_path = self.hooks_path / hook_name
                if not hook_path.exists():
                    with open(hook_path, "w") as f:
                        f.write(hook_func())
                    hook_path.chmod(0o755)

        except Exception as e:
            logger.error(f"Error setting up Git hooks: {e}")

    def _pre_commit_hook(self) -> str:
        """Generate pre-commit hook script."""
        return """#!/bin/sh
# Pre-commit hook for sniffing operations

# Get staged files
files=$(git diff --cached --name-only --diff-filter=ACM)

# Run sniffing on staged files
python -m sniffing.git.hooks.pre_commit $files

# Check result
if [ $? -ne 0 ]; then
    echo "Pre-commit sniffing failed. Please fix the issues before committing."
    exit 1
fi

exit 0
"""

    def _pre_push_hook(self) -> str:
        """Generate pre-push hook script."""
        return """#!/bin/sh
# Pre-push hook for sniffing operations

# Get commits to be pushed
while read local_ref local_sha remote_ref remote_sha
do
    # Run sniffing on changed files
    python -m sniffing.git.hooks.pre_push $local_sha $remote_sha

    # Check result
    if [ $? -ne 0 ]; then
        echo "Pre-push sniffing failed. Please fix the issues before pushing."
        exit 1
    fi
done

exit 0
"""

    def _post_commit_hook(self) -> str:
        """Generate post-commit hook script."""
        return """#!/bin/sh
# Post-commit hook for sniffing operations

# Get last commit hash
commit_hash=$(git rev-parse HEAD)

# Run post-commit operations
python -m sniffing.git.hooks.post_commit $commit_hash

exit 0
"""

    def _post_merge_hook(self) -> str:
        """Generate post-merge hook script."""
        return """#!/bin/sh
# Post-merge hook for sniffing operations

# Get changed files
files=$(git diff-tree -r --name-only --no-commit-id ORIG_HEAD HEAD)

# Run post-merge operations
python -m sniffing.git.hooks.post_merge $files

exit 0
"""

    async def check_branch_protection(self, branch: str) -> Dict[str, Any]:
        """Check branch protection rules."""
        try:
            # Get branch protection rules
            rules = self.config.get("branch_protection", {}).get(branch, {})
            if not rules:
                return {
                    "status": "unprotected",
                    "message": f"No protection rules found for branch {branch}"
                }

            # Check required checks
            required_checks = rules.get("required_checks", [])
            missing_checks = []
            for check in required_checks:
                if not await self._check_status(branch, check):
                    missing_checks.append(check)

            if missing_checks:
                return {
                    "status": "failed",
                    "message": f"Missing required checks: {', '.join(missing_checks)}"
                }

            return {
                "status": "protected",
                "message": "All protection rules satisfied"
            }

        except Exception as e:
            logger.error(f"Error checking branch protection: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    async def _check_status(self, branch: str, check: str) -> bool:
        """Check status of a specific check."""
        try:
            # Get latest commit
            commit = self.repo.heads[branch].commit

            # Check status
            if check == "sniffing":
                return await self._check_sniffing_status(commit)
            elif check == "tests":
                return await self._check_test_status(commit)
            elif check == "coverage":
                return await self._check_coverage_status(commit)
            else:
                return False

        except Exception as e:
            logger.error(f"Error checking status: {e}")
            return False

    async def _check_sniffing_status(self, commit: Any) -> bool:
        """Check sniffing status for a commit."""
        try:
            # Get changed files
            changed_files = self._get_changed_files(commit)

            # Run sniffing
            result = await self._run_sniffing(changed_files)
            return result.get("status") == "success"

        except Exception as e:
            logger.error(f"Error checking sniffing status: {e}")
            return False

    async def _check_test_status(self, commit: Any) -> bool:
        """Check test status for a commit."""
        try:
            # Get changed files
            changed_files = self._get_changed_files(commit)

            # Run tests
            result = await self._run_tests(changed_files)
            return result.get("status") == "success"

        except Exception as e:
            logger.error(f"Error checking test status: {e}")
            return False

    async def _check_coverage_status(self, commit: Any) -> bool:
        """Check coverage status for a commit."""
        try:
            # Get changed files
            changed_files = self._get_changed_files(commit)

            # Check coverage
            result = await self._check_coverage(changed_files)
            return result.get("status") == "success"

        except Exception as e:
            logger.error(f"Error checking coverage status: {e}")
            return False

    def _get_changed_files(self, commit: Any) -> Set[Path]:
        """Get files changed in a commit."""
        try:
            changed = set()

            # Get parent commit
            parent = commit.parents[0] if commit.parents else None
            if parent:
                # Get diff
                diff = parent.diff(commit)
                for item in diff:
                    if item.a_path:
                        changed.add(Path(item.a_path))
                    if item.b_path:
                        changed.add(Path(item.b_path))

            return changed

        except Exception as e:
            logger.error(f"Error getting changed files: {e}")
            return set()

    async def _run_sniffing(self, files: Set[Path]) -> Dict[str, Any]:
        """Run sniffing on files."""
        try:
            # Run sniffing command
            cmd = ["python", "-m", "sniffing"]
            cmd.extend(str(f) for f in files)

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()
            return {
                "status": "success" if process.returncode == 0 else "failure",
                "stdout": stdout.decode(),
                "stderr": stderr.decode()
            }

        except Exception as e:
            logger.error(f"Error running sniffing: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    async def _run_tests(self, files: Set[Path]) -> Dict[str, Any]:
        """Run tests for files."""
        try:
            # Run test command
            cmd = ["pytest"]
            cmd.extend(str(f) for f in files)

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()
            return {
                "status": "success" if process.returncode == 0 else "failure",
                "stdout": stdout.decode(),
                "stderr": stderr.decode()
            }

        except Exception as e:
            logger.error(f"Error running tests: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    async def _check_coverage(self, files: Set[Path]) -> Dict[str, Any]:
        """Check coverage for files."""
        try:
            # Run coverage command
            cmd = ["pytest", "--cov"]
            cmd.extend(str(f) for f in files)

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()
            return {
                "status": "success" if process.returncode == 0 else "failure",
                "stdout": stdout.decode(),
                "stderr": stderr.decode()
            }

        except Exception as e:
            logger.error(f"Error checking coverage: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    async def analyze_commit_history(self, branch: str) -> Dict[str, Any]:
        """Analyze commit history for a branch."""
        try:
            # Get branch
            branch_ref = self.repo.heads[branch]
            commits = list(self.repo.iter_commits(branch_ref))

            # Analyze commits
            analysis = {
                "total_commits": len(commits),
                "authors": set(),
                "file_changes": {},
                "commit_types": {},
                "issues": []
            }

            for commit in commits:
                # Add author
                analysis["authors"].add(commit.author.name)

                # Analyze message
                commit_type = self._get_commit_type(commit.message)
                analysis["commit_types"][commit_type] = analysis["commit_types"].get(commit_type, 0) + 1

                # Check for issues
                issues = self._check_commit_issues(commit)
                if issues:
                    analysis["issues"].extend(issues)

                # Track file changes
                for file in self._get_changed_files(commit):
                    if str(file) not in analysis["file_changes"]:
                        analysis["file_changes"][str(file)] = 0
                    analysis["file_changes"][str(file)] += 1

            return {
                "status": "success",
                "analysis": analysis
            }

        except Exception as e:
            logger.error(f"Error analyzing commit history: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    def _get_commit_type(self, message: str) -> str:
        """Get commit type from message."""
        types = {
            "feat": "feature",
            "fix": "bugfix",
            "docs": "documentation",
            "style": "style",
            "refactor": "refactor",
            "test": "test",
            "chore": "chore"
        }

        # Check conventional commit format
        first_line = message.split("\n")[0]
        for prefix, commit_type in types.items():
            if first_line.startswith(f"{prefix}:"):
                return commit_type

        return "other"

    def _check_commit_issues(self, commit: Any) -> List[Dict[str, Any]]:
        """Check for issues in a commit."""
        issues = []

        # Check message format
        if not self._is_valid_message_format(commit.message):
            issues.append({
                "type": "invalid_message",
                "commit": commit.hexsha,
                "message": "Invalid commit message format"
            })

        # Check file changes
        if len(self._get_changed_files(commit)) > 10:
            issues.append({
                "type": "large_commit",
                "commit": commit.hexsha,
                "message": "Too many files changed in single commit"
            })

        return issues

    def _is_valid_message_format(self, message: str) -> bool:
        """Check if commit message follows format."""
        # Check conventional commit format
        first_line = message.split("\n")[0]
        return any(
            first_line.startswith(f"{prefix}:") for prefix in [
                "feat", "fix", "docs", "style", "refactor", "test", "chore"
            ]
        )

    async def fix_commit_issues(self, issues: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Fix commit issues."""
        try:
            fixed = []
            failed = []

            for issue in issues:
                if issue["type"] == "invalid_message":
                    # Fix commit message
                    if await self._fix_commit_message(issue["commit"]):
                        fixed.append(issue)
                    else:
                        failed.append(issue)
                elif issue["type"] == "large_commit":
                    # Split commit
                    if await self._split_large_commit(issue["commit"]):
                        fixed.append(issue)
                    else:
                        failed.append(issue)

            return {
                "status": "success",
                "fixed": fixed,
                "failed": failed
            }

        except Exception as e:
            logger.error(f"Error fixing commit issues: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    async def _fix_commit_message(self, commit_hash: str) -> bool:
        """Fix commit message format."""
        try:
            # Get commit
            commit = self.repo.commit(commit_hash)

            # Parse current message
            message = commit.message
            first_line = message.split("\n")[0]

            # Add conventional commit prefix
            if not any(first_line.startswith(f"{prefix}:") for prefix in ["feat", "fix", "docs", "style", "refactor", "test", "chore"]):
                new_message = f"chore: {message}"
                self.repo.git.commit("--amend", "-m", new_message)
                return True

            return False

        except Exception as e:
            logger.error(f"Error fixing commit message: {e}")
            return False

    async def _split_large_commit(self, commit_hash: str) -> bool:
        """Split large commit into smaller ones."""
        try:
            # Get commit
            commit = self.repo.commit(commit_hash)

            # Get parent
            parent = commit.parents[0] if commit.parents else None
            if not parent:
                return False

            # Get changed files
            changed_files = list(self._get_changed_files(commit))
            if len(changed_files) <= 10:
                return False

            # Create new branch
            temp_branch = f"split-{commit_hash[:8]}"
            self.repo.git.checkout("-b", temp_branch, parent.hexsha)

            # Split changes
            for i in range(0, len(changed_files), 10):
                batch = changed_files[i:i + 10]
                # Add files
                for file in batch:
                    self.repo.git.add(str(file))
                # Commit
                self.repo.git.commit("-m", f"split({i//10 + 1}): {commit.message}")

            # Merge back
            current_branch = self.repo.active_branch.name
            self.repo.git.checkout(current_branch)
            self.repo.git.merge(temp_branch)
            self.repo.git.branch("-D", temp_branch)

            return True

        except Exception as e:
            logger.error(f"Error splitting commit: {e}")
            return False

    async def cleanup(self) -> None:
        """Clean up resources."""
        try:
            # Clean up temporary branches
            for branch in self.repo.heads:
                if branch.name.startswith("split-"):
                    self.repo.git.branch("-D", branch.name)

        except Exception as e:
            logger.error(f"Error cleaning up: {e}")
