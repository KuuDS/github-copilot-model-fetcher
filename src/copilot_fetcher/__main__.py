"""CLI entry point for GitHub Copilot model fetcher."""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

from copilot_fetcher.api import CopilotClient, CopilotAPIError
from copilot_fetcher.oauth import GitHubDeviceFlow, GitHubOAuthError, TokenResponse
from copilot_fetcher.storage import Storage, StoredToken


def get_client_id() -> str:
    """Get OAuth client ID from environment or prompt."""
    client_id = os.environ.get("GITHUB_CLIENT_ID")
    if not client_id:
        print("Error: GITHUB_CLIENT_ID environment variable not set")
        print("\nTo use this tool, you need to:")
        print("1. Create a GitHub OAuth App at https://github.com/settings/applications/new")
        print("2. Enable 'Device Flow' in the app settings")
        print("3. Set GITHUB_CLIENT_ID environment variable")
        print("\nExample:")
        print("  export GITHUB_CLIENT_ID=Ov23lixxx...")
        sys.exit(1)
    return client_id


def authenticate(storage: Storage, client_id: str, force: bool = False) -> str:
    """Authenticate and return access token.

    Args:
        storage: Storage instance
        client_id: OAuth client ID
        force: Force re-authentication even if token exists

    Returns:
        Access token string
    """
    # Check for existing token
    if not force:
        stored = storage.load_token()
        if stored:
            print(f"Using existing token (created: {stored.created_at})")
            return stored.access_token

    # Perform OAuth flow
    flow = GitHubDeviceFlow(client_id)

    try:
        token_response = flow.authenticate(open_browser=True)
    except GitHubOAuthError as e:
        print(f"Authentication failed: {e}")
        sys.exit(1)

    # Save token
    stored_token = StoredToken(
        access_token=token_response.access_token,
        token_type=token_response.token_type,
        scope=token_response.scope,
        created_at=datetime.now().isoformat(),
    )
    storage.save_token(stored_token)

    print(f"\n✓ Authentication successful!")
    print(f"✓ Token saved to: {storage.token_file}")

    return token_response.access_token


def fetch_models(access_token: str, storage: Storage) -> None:
    """Fetch and save Copilot models.

    Args:
        access_token: OAuth access token
        storage: Storage instance
    """
    print("\nFetching Copilot models...")

    try:
        with CopilotClient(access_token) as client:
            response = client.get_models()
    except CopilotAPIError as e:
        print(f"Failed to fetch models: {e}")
        sys.exit(1)

    # Save to storage
    storage.save_models(response)

    print(f"✓ Fetched {response.total} models")
    print(f"✓ Saved to: {storage.models_file}")


def list_models(storage: Storage) -> None:
    """Display stored models.

    Args:
        storage: Storage instance
    """
    stored = storage.load_models()
    if not stored:
        print("No models found. Run 'copilot-fetcher fetch' first.")
        sys.exit(1)

    print(f"\n{'=' * 80}")
    print(f"GitHub Copilot Models (fetched: {stored.fetched_at})")
    print(f"{'=' * 80}")

    for i, model in enumerate(stored.models, 1):
        name = model.get("name", "Unknown")
        model_id = model.get("id", "unknown")
        version = model.get("version", "")
        description = model.get("description") or "No description"
        provider = model.get("provider", "Unknown")
        capabilities = model.get("capabilities", [])

        print(f"\n{i}. {name}")
        print(f"   ID: {model_id}")
        print(f"   Version: {version}")
        print(f"   Provider: {provider}")
        print(f"   Description: {description}")
        if capabilities:
            print(f"   Capabilities: {', '.join(capabilities)}")

    print(f"\n{'=' * 80}")
    print(f"Total: {stored.total} models")
    print(f"{'=' * 80}\n")


def show_raw(storage: Storage) -> None:
    """Display raw JSON data.

    Args:
        storage: Storage instance
    """
    import json

    raw = storage.get_raw_models()
    if not raw:
        print("No models data found. Run 'copilot-fetcher fetch' first.")
        sys.exit(1)

    print(json.dumps(raw, indent=2, ensure_ascii=False))


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        prog="copilot-fetcher",
        description="Fetch GitHub Copilot models via OAuth",
    )

    parser.add_argument(
        "--data-dir",
        type=Path,
        default=None,
        help="Directory for data files (default: ~/.copilot-fetcher)",
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Auth command
    auth_parser = subparsers.add_parser(
        "auth",
        help="Authenticate with GitHub OAuth",
    )
    auth_parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-authentication",
    )

    # Fetch command
    fetch_parser = subparsers.add_parser(
        "fetch",
        help="Fetch and save Copilot models",
    )
    fetch_parser.add_argument(
        "--force-auth",
        action="store_true",
        help="Force re-authentication before fetching",
    )

    # List command
    subparsers.add_parser(
        "list",
        help="List fetched models",
    )

    # Raw command
    subparsers.add_parser(
        "raw",
        help="Show raw JSON data",
    )

    # Clear command
    subparsers.add_parser(
        "clear",
        help="Clear stored authentication and data",
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    storage = Storage(args.data_dir)

    if args.command == "auth":
        client_id = get_client_id()
        authenticate(storage, client_id, force=args.force)

    elif args.command == "fetch":
        client_id = get_client_id()
        access_token = authenticate(storage, client_id, force=args.force_auth)
        fetch_models(access_token, storage)

    elif args.command == "list":
        list_models(storage)

    elif args.command == "raw":
        show_raw(storage)

    elif args.command == "clear":
        storage.delete_token()
        if storage.models_file.exists():
            storage.models_file.unlink()
        print("✓ Cleared all stored data")

    return 0


if __name__ == "__main__":
    sys.exit(main())
