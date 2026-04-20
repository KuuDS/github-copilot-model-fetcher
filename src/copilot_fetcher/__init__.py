"""GitHub Copilot Model Fetcher.

A Python tool to fetch and store GitHub Copilot available models.

Supports multiple authentication methods:
1. GitHub CLI (gh) - For local development
2. GH_TOKEN environment variable - For CI/CD and GitHub Actions
3. OAuth Device Flow - For interactive GitHub Actions authentication

Usage:
    # Local development
    gh auth login
    python -m copilot_fetcher fetch

    # CI/CD with environment variable
    export GH_TOKEN="your_github_token"
    python -m copilot_fetcher fetch

    # GitHub Actions with device flow (manual trigger)
    # Set OAUTH_CLIENT_ID secret, then trigger workflow_dispatch

See README.md for detailed setup instructions.
"""

from copilot_fetcher.api import CopilotClient, CopilotModel, ModelsResponse
from copilot_fetcher.device_flow import (
    DeviceFlowError,
    is_device_flow_available,
    poll_for_token,
    run_device_flow,
    start_device_flow,
    update_repo_secret,
)
from copilot_fetcher.gh_auth import (
    check_gh_auth,
    get_gh_token,
    get_token_from_env,
    get_token_type,
    is_personal_access_token,
)
from copilot_fetcher.storage import Storage

__version__ = "0.1.0"
__all__ = [
    "CopilotClient",
    "CopilotModel",
    "ModelsResponse",
    "DeviceFlowError",
    "check_gh_auth",
    "get_gh_token",
    "get_token_from_env",
    "get_token_type",
    "is_personal_access_token",
    "is_device_flow_available",
    "run_device_flow",
    "start_device_flow",
    "poll_for_token",
    "update_repo_secret",
    "Storage",
]
