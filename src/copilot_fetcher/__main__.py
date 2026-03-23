"""CLI entry point for GitHub Copilot model fetcher."""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

from copilot_fetcher.api import CopilotClient, CopilotAPIError
from copilot_fetcher.gh_auth import check_gh_auth, get_gh_token, GitHubCLIError
from copilot_fetcher.oauth import GitHubDeviceFlow, GitHubOAuthError, TokenResponse
from copilot_fetcher.storage import Storage, StoredToken


def get_access_token(storage: Storage, force: bool = False) -> str:
    """Get access token using best available method.

    Priority:
    1. Use gh CLI token (recommended - provides full model list)
    2. Use stored OAuth token
    3. Perform OAuth Device Flow

    Args:
        storage: Storage instance
        force: Force re-authentication

    Returns:
        Access token string
    """
    # Check for stored token unless forcing re-auth
    if not force:
        stored = storage.load_token()
        if stored:
            print(f"Using stored token (created: {stored.created_at})")
            return stored.access_token

    # Try gh CLI first (preferred)
    gh_available, gh_message = check_gh_auth()
    if gh_available:
        try:
            token = get_gh_token()
            print("✓ Using GitHub CLI (gh) authentication")
            print("  This provides access to the full model list (35+ models)")

            # Save token for reuse
            stored_token = StoredToken(
                access_token=token,
                token_type="bearer",
                scope="",
                created_at=datetime.now().isoformat(),
            )
            storage.save_token(stored_token)

            return token
        except GitHubCLIError as e:
            print(f"Note: {e}")
            print("Falling back to OAuth authentication...\n")

    # Fall back to OAuth Device Flow
    print("Using OAuth Device Flow authentication")
    print("Note: This may return a limited model list (7 models)")
    print("For full access, install gh CLI: https://cli.github.com/\n")

    client_id = input("Enter your GitHub OAuth App Client ID: ").strip()
    if not client_id:
        print("Error: Client ID is required")
        sys.exit(1)

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

    # Group models by provider/family for better display
    models_by_family: dict[str, list[dict]] = {}
    for model in stored.models:
        model_id = model.get("id", "unknown")
        # Try to determine family from ID
        if "claude" in model_id.lower():
            family = "Anthropic Claude"
        elif "gpt" in model_id.lower():
            family = "OpenAI GPT"
        elif "gemini" in model_id.lower():
            family = "Google Gemini"
        elif "grok" in model_id.lower():
            family = "xAI Grok"
        else:
            family = "Other"

        if family not in models_by_family:
            models_by_family[family] = []
        models_by_family[family].append(model)

    # Display grouped models
    for family in sorted(models_by_family.keys()):
        print(f"\n【{family}】")
        for model in sorted(models_by_family[family], key=lambda m: m.get("id", "")):
            model_id = model.get("id", "unknown")
            name = model.get("name", model_id)
            print(f"  • {model_id}")
            if name != model_id:
                print(f"    ({name})")

    print(f"\n{'=' * 80}")
    print(f"Total: {stored.total} models")
    print(f"{'=' * 80}\n")

    # Show tip if limited models
    if stored.total <= 10:
        print("💡 Tip: For the full model list (35+ models including Claude, Gemini, GPT-5),")
        print("   authenticate using GitHub CLI (gh): https://cli.github.com/\n")


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


def show_auth_status() -> None:
    """Show authentication status."""
    print("\nAuthentication Status")
    print("=" * 60)

    # Check gh CLI
    gh_available, gh_message = check_gh_auth()
    if gh_available:
        print(f"✓ {gh_message}")
        print("  Token source: gh auth token")
        print("  Model access: FULL (35+ models)")
    else:
        print(f"✗ {gh_message}")
        print("  Install: https://cli.github.com/")
        print("  Then run: gh auth login")

    print()

    # Check OAuth
    import os

    client_id_env = "GITHUB_CLIENT_ID" in os.environ
    print(f"OAuth Device Flow:")
    print(f"  Environment: {'Configured' if client_id_env else 'Not configured'}")
    print(f"  Model access: LIMITED (7 models)")

    print("\n" + "=" * 60)
    print("\nRecommendation: Use GitHub CLI for full model access.\n")


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        prog="copilot-fetcher",
        description="Fetch GitHub Copilot models",
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
        help="Authenticate (uses gh CLI if available, else OAuth)",
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

    # Status command
    subparsers.add_parser(
        "status",
        help="Show authentication status",
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
        get_access_token(storage, force=args.force)

    elif args.command == "fetch":
        access_token = get_access_token(storage, force=args.force_auth)
        fetch_models(access_token, storage)

    elif args.command == "list":
        list_models(storage)

    elif args.command == "raw":
        show_raw(storage)

    elif args.command == "status":
        show_auth_status()

    elif args.command == "clear":
        storage.delete_token()
        if storage.models_file.exists():
            storage.models_file.unlink()
        print("✓ Cleared all stored data")

    return 0


if __name__ == "__main__":
    sys.exit(main())
