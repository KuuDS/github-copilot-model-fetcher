"""GitHub CLI authentication support."""

from __future__ import annotations

import os
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


def get_token_from_env() -> str | None:
    """Get token from environment variable.

    Returns:
        Token string if GH_TOKEN is set, None otherwise
    """
    return os.environ.get("GH_TOKEN")


def get_token_type(token: str) -> str:
    """Classify a GitHub token by its prefix.

    Args:
        token: GitHub token string

    Returns:
        Token type: "pat", "oauth", "app", or "unknown"
    """
    if not token:
        return "unknown"
    if token.startswith("ghp_") or token.startswith("github_pat_"):
        return "pat"
    if token.startswith("gho_"):
        return "oauth"
    if token.startswith("ghs_"):
        return "app"
    return "unknown"


def is_personal_access_token(token: str) -> bool:
    """Check if token is a Personal Access Token (rejected by Copilot API).

    Args:
        token: GitHub token string

    Returns:
        True if token is a PAT
    """
    return get_token_type(token) == "pat"


def get_gh_token() -> str:
    """Get authentication token from GitHub CLI or environment.

    Priority:
    1. GH_TOKEN environment variable (for CI/GitHub Actions)
    2. gh CLI auth token (for local development)

    Returns:
        GitHub token string

    Raises:
        GitHubCLIError: If no token is available
    """
    # First try environment variable (for GitHub Actions)
    env_token = get_token_from_env()
    if env_token:
        return env_token

    # Fall back to gh CLI
    return get_gh_token_from_cli()


def get_gh_token_from_cli() -> str:
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
            "Then run: gh auth login\n\n"
            "Or set GH_TOKEN environment variable."
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
            raise GitHubCLIError(
                "GitHub CLI is not authenticated.\n"
                "Please run: gh auth login\n\n"
                "Or set GH_TOKEN environment variable."
            )

        token = result.stdout.strip()
        if not token:
            raise GitHubCLIError(
                "GitHub CLI returned empty token.\n"
                "Please run: gh auth login\n\n"
                "Or set GH_TOKEN environment variable."
            )

        return token
    except subprocess.TimeoutExpired:
        raise GitHubCLIError("Timeout getting token from gh CLI")
    except Exception as e:
        raise GitHubCLIError(f"Error getting token from gh CLI: {e}") from e


def check_gh_auth() -> tuple[bool, str]:
    """Check if gh CLI is installed and authenticated.

    Also checks for GH_TOKEN environment variable.

    Returns:
        Tuple of (is_available, message)
    """
    # Check for GH_TOKEN first
    if get_token_from_env():
        return True, "GH_TOKEN environment variable is set"

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
        return False, "GitHub CLI (gh) not found and GH_TOKEN not set"
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
