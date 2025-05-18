"""
Git integration module for managing hooks and workflow.
"""
import os
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

import git
from git import Repo

class GitIntegration:
    """Manages Git integration and workflow hooks."""

    def __init__(self, repo_path: Optional[Path] = None):
        self.repo_path = repo_path or Path.cwd()
        self.repo = Repo(self.repo_path)
        self.hooks_dir = self.repo_path / ".git" / "hooks"

    def setup_hooks(self) -> None:
        """Set up all Git hooks."""
        hooks = {
            "pre-commit": self._pre_commit_hook,
            "pre-push": self._pre_push_hook,
            "post-merge": self._post_merge_hook
        }

        for hook_name, hook_content in hooks.items():
            self._create_hook(hook_name, hook_content)

    def _create_hook(self, hook_name: str, content: str) -> None:
        """Create a Git hook with the specified content."""
        hook_path = self.hooks_dir / hook_name

        # Ensure hooks directory exists
        self.hooks_dir.mkdir(parents=True, exist_ok=True)

        # Write hook content
        with open(hook_path, 'w') as f:
            f.write("#!/bin/sh\n")
            f.write(content)

        # Make hook executable
        hook_path.chmod(0o755)

    def get_changed_files(self) -> List[str]:
        """Get list of changed files in the working directory."""
        return [item.a_path for item in self.repo.index.diff(None)]

    def get_staged_files(self) -> List[str]:
        """Get list of staged files."""
        return [item.a_path for item in self.repo.index.diff("HEAD")]

    def get_commit_history(self, max_count: int = 10) -> List[Dict[str, Any]]:
        """Get recent commit history with details."""
        commits = []
        for commit in self.repo.iter_commits(max_count=max_count):
            commits.append({
                "hash": commit.hexsha,
                "author": str(commit.author),
                "date": commit.committed_datetime.isoformat(),
                "message": commit.message.strip(),
                "files": list(commit.stats.files.keys())
            })
        return commits

    def create_audit_commit(self, audit_data: Dict[str, Any]) -> str:
        """Create a commit with audit information."""
        # Create audit log file
        audit_path = self.repo_path / "audit" / "logs" / f"audit_{audit_data['timestamp']}.json"
        audit_path.parent.mkdir(parents=True, exist_ok=True)

        with open(audit_path, 'w') as f:
            import json
            json.dump(audit_data, f, indent=2)

        # Stage and commit audit file
        self.repo.index.add([str(audit_path)])
        commit = self.repo.index.commit(
            f"Audit: {audit_data.get('summary', 'Automated audit commit')}"
        )

        return commit.hexsha

    @property
    def _pre_commit_hook(self) -> str:
        return """
# Run sniffing checks
python -m sniffing.run_checks --pre-commit

# Store the exit code
exit_code=$?

# Exit with the stored exit code
exit $exit_code
"""

    @property
    def _pre_push_hook(self) -> str:
        return """
# Run comprehensive checks before push
python -m sniffing.run_checks --pre-push --comprehensive

# Store the exit code
exit_code=$?

# Exit with the stored exit code
exit $exit_code
"""

    @property
    def _post_merge_hook(self) -> str:
        return """
# Run post-merge checks and updates
python -m sniffing.run_checks --post-merge --update-dependencies

# Store the exit code
exit_code=$?

# Exit with the stored exit code
exit $exit_code
"""

    def validate_branch_policies(self) -> Dict[str, bool]:
        """Validate branch policies and protection rules."""
        current = self.repo.active_branch

        return {
            "protected_branch": current.name in ["main", "master", "develop"],
            "has_required_reviews": self._check_required_reviews(),
            "passing_checks": self._check_status_checks(),
            "up_to_date": not self.repo.is_dirty()
        }

    def _check_required_reviews(self) -> bool:
        """Check if required reviews are in place."""
        # Implementation would check GitHub/GitLab API
        return True

    def _check_status_checks(self) -> bool:
        """Check if status checks are passing."""
        # Implementation would check CI/CD status
        return True
