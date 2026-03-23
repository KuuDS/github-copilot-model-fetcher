"""GitHub Copilot Model Fetcher.

A Python tool to fetch and store GitHub Copilot available models via OAuth authentication.

Usage:
    export GITHUB_CLIENT_ID=your_oauth_app_client_id
    python -m copilot_fetcher auth
    python -m copilot_fetcher fetch
    python -m copilot_fetcher list

See README.md for detailed setup instructions.
"""

from copilot_fetcher.api import CopilotClient, CopilotModel, ModelsResponse
from copilot_fetcher.oauth import GitHubDeviceFlow, get_access_token
from copilot_fetcher.storage import Storage

__version__ = "0.1.0"
__all__ = [
    "CopilotClient",
    "CopilotModel",
    "ModelsResponse",
    "GitHubDeviceFlow",
    "get_access_token",
    "Storage",
]
