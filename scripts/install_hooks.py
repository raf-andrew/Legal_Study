"""
Script to install Git hooks.
"""
import os
import shutil
import stat
from pathlib import Path

def install_hooks() -> None:
    """Install Git hooks."""
    try:
        # Get paths
        hooks_dir = Path(".git/hooks")
        source_dir = Path("sniffing/git/hooks")

        # Create hooks directory if it doesn't exist
        hooks_dir.mkdir(parents=True, exist_ok=True)

        # Install pre-commit hook
        pre_commit_src = source_dir / "pre_commit.py"
        pre_commit_dst = hooks_dir / "pre-commit"
        shutil.copy2(pre_commit_src, pre_commit_dst)
        os.chmod(pre_commit_dst, stat.S_IRWXU)

        # Install pre-push hook
        pre_push_src = source_dir / "pre_push.py"
        pre_push_dst = hooks_dir / "pre-push"
        shutil.copy2(pre_push_src, pre_push_dst)
        os.chmod(pre_push_dst, stat.S_IRWXU)

        print("Git hooks installed successfully!")

    except Exception as e:
        print(f"Error installing Git hooks: {e}")
        raise

if __name__ == "__main__":
    install_hooks()
