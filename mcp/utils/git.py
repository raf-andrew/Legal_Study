"""
MCP Git integration utilities.
"""
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import git

logger = logging.getLogger("mcp_git")

class GitIntegration:
    """Git integration manager."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize Git integration.

        Args:
            config: Git configuration
        """
        self.config = config
        self.repo = self._init_repo()

    def _init_repo(self) -> git.Repo:
        """Initialize Git repository.

        Returns:
            Git repository
        """
        try:
            # Get workspace path
            workspace_path = Path(self.config["workspace_path"])
            if not workspace_path.exists():
                raise ValueError(f"Workspace not found: {workspace_path}")

            # Initialize repository
            return git.Repo(workspace_path)

        except Exception as e:
            logger.error(f"Error initializing repository: {e}")
            raise

    def get_changed_files(self) -> List[str]:
        """Get changed files.

        Returns:
            List of changed file paths
        """
        try:
            changed_files = []

            # Get staged changes
            staged = self.repo.index.diff("HEAD")
            for item in staged:
                if item.a_path:
                    changed_files.append(item.a_path)
                if item.b_path and item.b_path != item.a_path:
                    changed_files.append(item.b_path)

            # Get unstaged changes
            unstaged = self.repo.index.diff(None)
            for item in unstaged:
                if item.a_path:
                    changed_files.append(item.a_path)
                if item.b_path and item.b_path != item.a_path:
                    changed_files.append(item.b_path)

            # Get untracked files
            untracked = self.repo.untracked_files
            changed_files.extend(untracked)

            return list(set(changed_files))

        except Exception as e:
            logger.error(f"Error getting changed files: {e}")
            return []

    def get_file_history(self, file_path: str) -> List[Dict[str, Any]]:
        """Get file history.

        Args:
            file_path: File path

        Returns:
            List of commit dictionaries
        """
        try:
            history = []

            # Get file history
            for commit in self.repo.iter_commits(paths=file_path):
                history.append({
                    "hash": commit.hexsha,
                    "author": str(commit.author),
                    "date": commit.authored_datetime,
                    "message": commit.message.strip(),
                    "files": list(commit.stats.files.keys())
                })

            return history

        except Exception as e:
            logger.error(f"Error getting file history: {e}")
            return []

    def create_branch(self, branch_name: str) -> bool:
        """Create Git branch.

        Args:
            branch_name: Branch name

        Returns:
            Whether branch was created
        """
        try:
            # Create branch
            self.repo.create_head(branch_name)
            logger.info(f"Created branch: {branch_name}")
            return True

        except Exception as e:
            logger.error(f"Error creating branch: {e}")
            return False

    def switch_branch(self, branch_name: str) -> bool:
        """Switch Git branch.

        Args:
            branch_name: Branch name

        Returns:
            Whether branch was switched
        """
        try:
            # Get branch
            branch = self.repo.heads[branch_name]
            if not branch:
                raise ValueError(f"Branch not found: {branch_name}")

            # Switch branch
            branch.checkout()
            logger.info(f"Switched to branch: {branch_name}")
            return True

        except Exception as e:
            logger.error(f"Error switching branch: {e}")
            return False

    def stage_files(self, files: List[str]) -> bool:
        """Stage files.

        Args:
            files: Files to stage

        Returns:
            Whether files were staged
        """
        try:
            # Stage files
            self.repo.index.add(files)
            logger.info(f"Staged files: {files}")
            return True

        except Exception as e:
            logger.error(f"Error staging files: {e}")
            return False

    def commit_changes(
        self,
        message: str,
        files: Optional[List[str]] = None
    ) -> bool:
        """Commit changes.

        Args:
            message: Commit message
            files: Optional files to commit

        Returns:
            Whether changes were committed
        """
        try:
            # Stage files if provided
            if files:
                self.repo.index.add(files)

            # Commit changes
            self.repo.index.commit(message)
            logger.info(f"Committed changes: {message}")
            return True

        except Exception as e:
            logger.error(f"Error committing changes: {e}")
            return False

    def push_changes(
        self,
        branch: Optional[str] = None,
        remote: str = "origin"
    ) -> bool:
        """Push changes.

        Args:
            branch: Optional branch name
            remote: Remote name

        Returns:
            Whether changes were pushed
        """
        try:
            # Get remote
            git_remote = self.repo.remote(remote)
            if not git_remote:
                raise ValueError(f"Remote not found: {remote}")

            # Push changes
            if branch:
                git_remote.push(branch)
            else:
                git_remote.push()

            logger.info(f"Pushed changes to {remote}")
            return True

        except Exception as e:
            logger.error(f"Error pushing changes: {e}")
            return False

    def pull_changes(
        self,
        branch: Optional[str] = None,
        remote: str = "origin"
    ) -> bool:
        """Pull changes.

        Args:
            branch: Optional branch name
            remote: Remote name

        Returns:
            Whether changes were pulled
        """
        try:
            # Get remote
            git_remote = self.repo.remote(remote)
            if not git_remote:
                raise ValueError(f"Remote not found: {remote}")

            # Pull changes
            if branch:
                git_remote.pull(branch)
            else:
                git_remote.pull()

            logger.info(f"Pulled changes from {remote}")
            return True

        except Exception as e:
            logger.error(f"Error pulling changes: {e}")
            return False

    def get_current_branch(self) -> Optional[str]:
        """Get current branch name.

        Returns:
            Current branch name or None
        """
        try:
            return self.repo.active_branch.name

        except Exception as e:
            logger.error(f"Error getting current branch: {e}")
            return None

    def get_branches(self) -> List[str]:
        """Get branch names.

        Returns:
            List of branch names
        """
        try:
            return [head.name for head in self.repo.heads]

        except Exception as e:
            logger.error(f"Error getting branches: {e}")
            return []

    def get_remotes(self) -> List[str]:
        """Get remote names.

        Returns:
            List of remote names
        """
        try:
            return [remote.name for remote in self.repo.remotes]

        except Exception as e:
            logger.error(f"Error getting remotes: {e}")
            return []

    def get_tags(self) -> List[str]:
        """Get tag names.

        Returns:
            List of tag names
        """
        try:
            return [tag.name for tag in self.repo.tags]

        except Exception as e:
            logger.error(f"Error getting tags: {e}")
            return []

    def create_tag(
        self,
        tag_name: str,
        message: Optional[str] = None
    ) -> bool:
        """Create tag.

        Args:
            tag_name: Tag name
            message: Optional tag message

        Returns:
            Whether tag was created
        """
        try:
            # Create tag
            self.repo.create_tag(tag_name, message=message)
            logger.info(f"Created tag: {tag_name}")
            return True

        except Exception as e:
            logger.error(f"Error creating tag: {e}")
            return False

    def delete_tag(self, tag_name: str) -> bool:
        """Delete tag.

        Args:
            tag_name: Tag name

        Returns:
            Whether tag was deleted
        """
        try:
            # Delete tag
            self.repo.delete_tag(tag_name)
            logger.info(f"Deleted tag: {tag_name}")
            return True

        except Exception as e:
            logger.error(f"Error deleting tag: {e}")
            return False

    def get_commit(self, commit_hash: str) -> Optional[Dict[str, Any]]:
        """Get commit details.

        Args:
            commit_hash: Commit hash

        Returns:
            Commit dictionary or None
        """
        try:
            # Get commit
            commit = self.repo.commit(commit_hash)
            return {
                "hash": commit.hexsha,
                "author": str(commit.author),
                "date": commit.authored_datetime,
                "message": commit.message.strip(),
                "files": list(commit.stats.files.keys())
            }

        except Exception as e:
            logger.error(f"Error getting commit: {e}")
            return None

    def get_commits(
        self,
        branch: Optional[str] = None,
        max_count: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get commit history.

        Args:
            branch: Optional branch name
            max_count: Optional maximum number of commits

        Returns:
            List of commit dictionaries
        """
        try:
            commits = []

            # Get commits
            for commit in self.repo.iter_commits(branch, max_count=max_count):
                commits.append({
                    "hash": commit.hexsha,
                    "author": str(commit.author),
                    "date": commit.authored_datetime,
                    "message": commit.message.strip(),
                    "files": list(commit.stats.files.keys())
                })

            return commits

        except Exception as e:
            logger.error(f"Error getting commits: {e}")
            return []

    def get_diff(
        self,
        commit_a: str,
        commit_b: str
    ) -> List[Dict[str, Any]]:
        """Get diff between commits.

        Args:
            commit_a: First commit
            commit_b: Second commit

        Returns:
            List of diff dictionaries
        """
        try:
            diffs = []

            # Get diff
            diff_index = self.repo.commit(commit_a).diff(commit_b)
            for diff in diff_index:
                diffs.append({
                    "a_path": diff.a_path,
                    "b_path": diff.b_path,
                    "change_type": diff.change_type,
                    "renamed": diff.renamed,
                    "deleted": diff.deleted,
                    "new": diff.new
                })

            return diffs

        except Exception as e:
            logger.error(f"Error getting diff: {e}")
            return []

    def get_status(self) -> Dict[str, Any]:
        """Get repository status.

        Returns:
            Status dictionary
        """
        try:
            return {
                "branch": self.get_current_branch(),
                "changed_files": self.get_changed_files(),
                "branches": self.get_branches(),
                "remotes": self.get_remotes(),
                "tags": self.get_tags(),
                "timestamp": datetime.now()
            }

        except Exception as e:
            logger.error(f"Error getting status: {e}")
            return {}
