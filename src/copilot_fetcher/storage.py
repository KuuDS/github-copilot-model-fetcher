"""Data storage and persistence."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from copilot_fetcher.api import ModelsResponse


@dataclass
class StoredToken:
    """Stored OAuth token with metadata."""

    access_token: str
    token_type: str
    scope: str
    created_at: str
    expires_at: str | None = None


@dataclass
class StoredModels:
    """Stored models data with metadata."""

    models: list[dict[str, Any]]
    total: int
    fetched_at: str
    api_version: str = "v1"


class Storage:
    """File-based storage for tokens and API responses."""

    def __init__(self, data_dir: Path | str | None = None) -> None:
        """Initialize storage.

        Args:
            data_dir: Directory for data files (default: ~/.copilot-fetcher)
        """
        if data_dir is None:
            data_dir = Path.home() / ".copilot-fetcher"

        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.token_file = self.data_dir / "token.json"
        self.models_file = self.data_dir / "models.json"

    def save_token(self, token_response: StoredToken) -> None:
        """Save OAuth token to file.

        Args:
            token_response: Token data to save
        """
        data = {
            "access_token": token_response.access_token,
            "token_type": token_response.token_type,
            "scope": token_response.scope,
            "created_at": token_response.created_at,
            "expires_at": token_response.expires_at,
        }

        with open(self.token_file, "w") as f:
            json.dump(data, f, indent=2)

        # Secure the token file
        self.token_file.chmod(0o600)

    def load_token(self) -> StoredToken | None:
        """Load OAuth token from file.

        Returns:
            StoredToken if exists, None otherwise
        """
        if not self.token_file.exists():
            return None

        try:
            with open(self.token_file) as f:
                data = json.load(f)

            return StoredToken(
                access_token=data["access_token"],
                token_type=data.get("token_type", "bearer"),
                scope=data.get("scope", ""),
                created_at=data["created_at"],
                expires_at=data.get("expires_at"),
            )
        except (json.JSONDecodeError, KeyError):
            return None

    def delete_token(self) -> None:
        """Delete stored token."""
        if self.token_file.exists():
            self.token_file.unlink()

    def save_models(self, models_response: ModelsResponse) -> None:
        """Save models response to JSON file.

        Args:
            models_response: Models data to save
        """
        data = {
            "data": [asdict(model) for model in models_response.models],
            "total": models_response.total,
            "fetched_at": datetime.now().isoformat(),
            "api_version": "v1",
        }

        with open(self.models_file, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def load_models(self) -> StoredModels | None:
        """Load stored models from file.

        Returns:
            StoredModels if exists, None otherwise
        """
        if not self.models_file.exists():
            return None

        try:
            with open(self.models_file) as f:
                data = json.load(f)

            return StoredModels(
                models=data.get("data", []),
                total=data.get("total", 0),
                fetched_at=data.get("fetched_at", ""),
                api_version=data.get("api_version", "v1"),
            )
        except (json.JSONDecodeError, KeyError):
            return None

    def get_models_file_path(self) -> Path:
        """Get path to models JSON file.

        Returns:
            Path to models.json
        """
        return self.models_file

    def get_raw_models(self) -> dict[str, Any] | None:
        """Get raw models JSON data.

        Returns:
            Raw JSON data if exists, None otherwise
        """
        if not self.models_file.exists():
            return None

        try:
            with open(self.models_file) as f:
                return json.load(f)
        except json.JSONDecodeError:
            return None
