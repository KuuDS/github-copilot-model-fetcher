"""GitHub CLI authentication support."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass


class GitHubCLIError(Exception):
    """GitHub CLI error."""

    pass


@dataclass
class GHAuthToken:
    """GitHub CLI authentication token."""

    token: str
    source: str = "gh_cli"


def get_gh_token() -> str:
    """Get authentication token from GitHub CLI.

    Returns:
        GitHub token string

    Raises:
        GitHubCLIError: If gh CLI is not installed or not authenticated
    """
    # Check if gh CLI is installed
    try:
        result = subprocess.run(
            ["gh", "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            raise GitHubCLIError("GitHub CLI (gh) is not installed")
    except FileNotFoundError:
        raise GitHubCLIError(
            "GitHub CLI (gh) is not installed.\n"
            "Install from: https://cli.github.com/\n"
            "Then run: gh auth login"
        )

    # Get token from gh CLI
    try:
        result = subprocess.run(
            ["gh", "auth", "token"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            raise GitHubCLIError("GitHub CLI is not authenticated.\nPlease run: gh auth login")

        token = result.stdout.strip()
        if not token:
            raise GitHubCLIError("GitHub CLI returned empty token")

        return token
    except subprocess.TimeoutExpired:
        raise GitHubCLIError("Timeout getting token from gh CLI")
    except Exception as e:
        raise GitHubCLIError(f"Error getting token from gh CLI: {e}") from e


def check_gh_auth() -> tuple[bool, str]:
    """Check if gh CLI is installed and authenticated.

    Returns:
        Tuple of (is_available, message)
    """
    # Check if gh is installed
    try:
        result = subprocess.run(
            ["gh", "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode != 0:
            return False, "GitHub CLI (gh) not found"
    except FileNotFoundError:
        return False, "GitHub CLI (gh) not found"
    except Exception as e:
        return False, f"Error checking gh CLI: {e}"

    # Check if authenticated
    try:
        result = subprocess.run(
            ["gh", "auth", "status"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return True, "GitHub CLI is installed and authenticated"
        else:
            return False, "GitHub CLI is installed but not authenticated. Run: gh auth login"
    except Exception as e:
        return False, f"Error checking gh auth status: {e}"
