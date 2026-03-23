"""GitHub Copilot Model Fetcher.

A Python tool to fetch and store GitHub Copilot available models.

Supports two authentication methods:
1. GitHub CLI (gh) - Recommended, provides full model list (35+)
2. OAuth Device Flow - Limited model list (7 models)

Usage:
    # Using GitHub CLI (recommended)
    gh auth login
    python -m copilot_fetcher fetch

    # Using OAuth Device Flow
    export GITHUB_CLIENT_ID=your_oauth_app_client_id
    python -m copilot_fetcher auth
    python -m copilot_fetcher fetch

See README.md for detailed setup instructions.
"""

from copilot_fetcher.api import CopilotClient, CopilotModel, ModelsResponse
from copilot_fetcher.gh_auth import check_gh_auth, get_gh_token
from copilot_fetcher.oauth import GitHubDeviceFlow, get_access_token
from copilot_fetcher.storage import Storage

__version__ = "0.1.0"
__all__ = [
    "CopilotClient",
    "CopilotModel",
    "ModelsResponse",
    "GitHubDeviceFlow",
    "get_access_token",
    "check_gh_auth",
    "get_gh_token",
    "Storage",
]
