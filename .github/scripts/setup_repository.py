#!/usr/bin/env python3

import os
import sys
import json
import requests
from typing import Dict, Any

def setup_branch_protection(token: str, owner: str, repo: str) -> None:
    """Set up branch protection rules for the main branch."""
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"token {token}",
    }

    url = f"https://api.github.com/repos/{owner}/{repo}/branches/main/protection"

    data = {
        "required_status_checks": {
            "strict": True,
            "contexts": []
        },
        "enforce_admins": True,
        "required_pull_request_reviews": {
            "dismissal_restrictions": {},
            "dismiss_stale_reviews": True,
            "require_code_owner_reviews": True,
            "required_approving_review_count": 1
        },
        "restrictions": None
    }

    response = requests.put(url, headers=headers, json=data)

    if response.status_code == 200:
        print("✅ Branch protection rules set successfully")
    else:
        print(f"❌ Failed to set branch protection rules: {response.text}")
        sys.exit(1)

def setup_repository_settings(token: str, owner: str, repo: str) -> None:
    """Set up repository settings."""
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"token {token}",
    }

    url = f"https://api.github.com/repos/{owner}/{repo}"

    data = {
        "has_issues": True,
        "has_projects": True,
        "has_wiki": True,
        "has_discussions": True,
        "allow_squash_merge": True,
        "allow_merge_commit": True,
        "allow_rebase_merge": True,
        "delete_branch_on_merge": True,
        "allow_auto_merge": True,
        "allow_update_branch": True
    }

    response = requests.patch(url, headers=headers, json=data)

    if response.status_code == 200:
        print("✅ Repository settings updated successfully")
    else:
        print(f"❌ Failed to update repository settings: {response.text}")
        sys.exit(1)

def main() -> None:
    """Main function to set up repository configuration."""
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print("❌ GITHUB_TOKEN environment variable not set")
        sys.exit(1)

    owner = "raf-andrew"
    repo = "Legal_Study"

    print("Setting up repository configuration...")

    setup_repository_settings(token, owner, repo)
    setup_branch_protection(token, owner, repo)

    print("✅ Repository configuration completed successfully")

if __name__ == "__main__":
    main()
