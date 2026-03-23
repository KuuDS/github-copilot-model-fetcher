"""GitHub Copilot Model Fetcher.

A Python tool to fetch and store GitHub Copilot available models.

Requires GitHub CLI (gh) for authentication.

Usage:
    gh auth login
    python -m copilot_fetcher fetch
    python -m copilot_fetcher list

See README.md for detailed setup instructions.
"""

from copilot_fetcher.api import CopilotClient, CopilotModel, ModelsResponse
from copilot_fetcher.gh_auth import check_gh_auth, get_gh_token
from copilot_fetcher.storage import Storage

__version__ = "0.1.0"
__all__ = [
    "CopilotClient",
    "CopilotModel",
    "ModelsResponse",
    "check_gh_auth",
    "get_gh_token",
    "Storage",
]
