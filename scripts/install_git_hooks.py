"""
Script to install Git hooks for sniffing integration.
"""
import logging
import os
import shutil
import sys
from pathlib import Path
from typing import Dict, List

from rich.console import Console

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("git_hooks")

class GitHookInstaller:
    """Installer for Git hooks."""

    def __init__(self):
        self.console = Console()
        self.repo_root = self._find_repo_root()
        self.hooks_dir = self.repo_root / ".git" / "hooks"
        self.source_dir = Path("sniffing/git/hooks")

    def _find_repo_root(self) -> Path:
        """Find Git repository root."""
        current = Path.cwd()
        while current != current.parent:
            if (current / ".git").is_dir():
                return current
            current = current.parent
        raise FileNotFoundError("Not in a Git repository")

    def install_hooks(self) -> None:
        """Install Git hooks."""
        try:
            self.console.print("[bold green]Installing Git hooks...[/bold green]")

            # Create hooks directory
            self.hooks_dir.mkdir(parents=True, exist_ok=True)

            # Install hooks
            hooks = {
                "pre-commit": self._get_pre_commit_hook(),
                "pre-push": self._get_pre_push_hook(),
                "post-commit": self._get_post_commit_hook(),
                "post-merge": self._get_post_merge_hook()
            }

            for hook_name, hook_content in hooks.items():
                self._install_hook(hook_name, hook_content)

            self.console.print("[bold green]Git hooks installed successfully![/bold green]")

        except Exception as e:
            logger.error(f"Error installing Git hooks: {e}")
            sys.exit(1)

    def _install_hook(self, name: str, content: str) -> None:
        """Install a single Git hook."""
        try:
            hook_path = self.hooks_dir / name

            # Backup existing hook
            if hook_path.exists():
                backup_path = hook_path.with_suffix(".backup")
                shutil.copy2(hook_path, backup_path)
                self.console.print(f"Backed up existing {name} hook to {backup_path}")

            # Write new hook
            with open(hook_path, "w") as f:
                f.write(content)

            # Make executable
            hook_path.chmod(0o755)
            self.console.print(f"Installed {name} hook")

        except Exception as e:
            logger.error(f"Error installing {name} hook: {e}")
            raise

    def _get_pre_commit_hook(self) -> str:
        """Get pre-commit hook content."""
        return '''#!/bin/sh
# Pre-commit hook for sniffing operations

# Exit on error
set -e

# Get staged files
files=$(git diff --cached --name-only --diff-filter=ACM)

if [ -z "$files" ]; then
    echo "No files to check"
    exit 0
fi

echo "Running sniffing checks..."

# Run sniffing on staged files
python -m sniffing.git.hooks.pre_commit $files

# Check result
if [ $? -ne 0 ]; then
    echo "❌ Pre-commit sniffing failed"
    echo "Please fix the issues before committing"
    exit 1
fi

echo "✅ Pre-commit sniffing passed"
exit 0
'''

    def _get_pre_push_hook(self) -> str:
        """Get pre-push hook content."""
        return '''#!/bin/sh
# Pre-push hook for sniffing operations

# Exit on error
set -e

# Get commits to be pushed
while read local_ref local_sha remote_ref remote_sha
do
    # Skip if pushing tags
    if [ "$local_sha" = "0000000000000000000000000000000000000000" ]; then
        continue
    fi

    echo "Running sniffing checks..."

    # Run sniffing on changed files
    python -m sniffing.git.hooks.pre_push $local_sha $remote_sha

    # Check result
    if [ $? -ne 0 ]; then
        echo "❌ Pre-push sniffing failed"
        echo "Please fix the issues before pushing"
        exit 1
    fi
done

echo "✅ Pre-push sniffing passed"
exit 0
'''

    def _get_post_commit_hook(self) -> str:
        """Get post-commit hook content."""
        return '''#!/bin/sh
# Post-commit hook for sniffing operations

# Get last commit hash
commit_hash=$(git rev-parse HEAD)

echo "Running post-commit operations..."

# Run post-commit operations
python -m sniffing.git.hooks.post_commit $commit_hash

# Note: We don't exit with error as this is a post-commit hook
exit 0
'''

    def _get_post_merge_hook(self) -> str:
        """Get post-merge hook content."""
        return '''#!/bin/sh
# Post-merge hook for sniffing operations

# Get changed files
files=$(git diff-tree -r --name-only --no-commit-id ORIG_HEAD HEAD)

if [ -z "$files" ]; then
    echo "No files changed in merge"
    exit 0
fi

echo "Running post-merge operations..."

# Run post-merge operations
python -m sniffing.git.hooks.post_merge $files

# Note: We don't exit with error as this is a post-merge hook
exit 0
'''

def main() -> None:
    """Main entry point."""
    installer = GitHookInstaller()
    installer.install_hooks()

if __name__ == "__main__":
    main()
