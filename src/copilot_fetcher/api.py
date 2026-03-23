"""GitHub Copilot API client."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import httpx


@dataclass
class CopilotModel:
    """GitHub Copilot model information."""

    id: str
    name: str
    version: str
    description: str | None = None
    capabilities: dict[str, Any] = field(default_factory=dict)
    limits: dict[str, Any] = field(default_factory=dict)
    provider: str | None = None


@dataclass
class ModelsResponse:
    """Response from /models endpoint."""

    models: list[CopilotModel]
    total: int


class CopilotAPIError(Exception):
    """Copilot API error."""

    pass


class CopilotClient:
    """Client for GitHub Copilot API."""

    BASE_URL = "https://api.githubcopilot.com"

    def __init__(self, access_token: str) -> None:
        """Initialize with access token.

        Args:
            access_token: OAuth access token (prefix: gho_)
        """
        self.access_token = access_token
        self.client = httpx.Client(
            base_url=self.BASE_URL,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json",
            },
            timeout=30.0,
        )

    def __enter__(self) -> CopilotClient:
        """Context manager entry."""
        return self

    def __exit__(self, *args: Any) -> None:
        """Context manager exit."""
        self.close()

    def close(self) -> None:
        """Close HTTP client."""
        self.client.close()

    def _handle_error(self, response: httpx.Response) -> None:
        """Handle API error responses."""
        if response.status_code >= 400:
            try:
                error_data = response.json()
                message = error_data.get("message") or error_data.get("error", {}).get(
                    "message", "Unknown error"
                )
            except Exception:
                message = response.text or "Unknown error"

            raise CopilotAPIError(f"API error {response.status_code}: {message}")

    def get_models(self) -> ModelsResponse:
        """Fetch available Copilot models.

        Returns:
            ModelsResponse with list of models

        Raises:
            CopilotAPIError: If API request fails
        """
        try:
            response = self.client.get("/models")
            self._handle_error(response)
            data = response.json()

            models = []
            for model_data in data.get("data", []):
                model = CopilotModel(
                    id=model_data.get("id", ""),
                    name=model_data.get("name", ""),
                    version=model_data.get("version", ""),
                    description=model_data.get("description"),
                    capabilities=model_data.get("capabilities", {}),
                    limits=model_data.get("limits", {}),
                    provider=model_data.get("provider"),
                )
                models.append(model)

            return ModelsResponse(
                models=models,
                total=data.get("total", len(models)),
            )

        except httpx.HTTPStatusError as e:
            raise CopilotAPIError(f"HTTP error fetching models: {e}") from e
        except httpx.RequestError as e:
            raise CopilotAPIError(f"Network error fetching models: {e}") from e

    def get_model(self, model_id: str) -> CopilotModel:
        """Fetch specific model details.

        Args:
            model_id: Model identifier

        Returns:
            CopilotModel details
        """
        try:
            response = self.client.get(f"/models/{model_id}")
            self._handle_error(response)
            data = response.json()

            return CopilotModel(
                id=data.get("id", ""),
                name=data.get("name", ""),
                version=data.get("version", ""),
                description=data.get("description"),
                capabilities=data.get("capabilities", {}),
                limits=data.get("limits", {}),
                provider=data.get("provider"),
            )

        except httpx.HTTPStatusError as e:
            raise CopilotAPIError(f"HTTP error fetching model: {e}") from e
        except httpx.RequestError as e:
            raise CopilotAPIError(f"Network error fetching model: {e}") from e
