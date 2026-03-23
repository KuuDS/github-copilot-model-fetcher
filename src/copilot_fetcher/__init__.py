"""GitHub Copilot Model Fetcher.

A Python tool to fetch and store GitHub Copilot available models.

Supports two authentication methods:
1. GitHub CLI (gh) - For local development
2. GH_TOKEN environment variable - For CI/CD and GitHub Actions

Usage:
    # Local development
    gh auth login
    python -m copilot_fetcher fetch

    # CI/CD with environment variable
    export GH_TOKEN="your_github_token"
    python -m copilot_fetcher fetch

See README.md for detailed setup instructions.
"""

from copilot_fetcher.api import CopilotClient, CopilotModel, ModelsResponse
from copilot_fetcher.gh_auth import check_gh_auth, get_gh_token, get_token_from_env
from copilot_fetcher.storage import Storage

__version__ = "0.1.0"
__all__ = [
    "CopilotClient",
    "CopilotModel",
    "ModelsResponse",
    "check_gh_auth",
    "get_gh_token",
    "get_token_from_env",
    "Storage",
]
