"""CLI entry point for GitHub Copilot model fetcher."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

from copilot_fetcher.api import CopilotAPIError, CopilotClient
from copilot_fetcher.device_flow import DeviceFlowError, is_device_flow_available, run_device_flow
from copilot_fetcher.gh_auth import (
    GitHubCLIError,
    check_gh_auth,
    get_gh_token,
    get_token_from_env,
    get_token_type,
)
from copilot_fetcher.storage import Storage, StoredToken

# Global start time for execution timeout check
_START_TIME = time.time()
_MAX_EXECUTION_SECONDS = 30 * 60  # 30 minutes
_MAX_TOKEN_FAILURES = 3


def _check_timeout() -> None:
    """Check if total execution time exceeds the maximum allowed."""
    elapsed = time.time() - _START_TIME
    if elapsed > _MAX_EXECUTION_SECONDS:
        print(f"Error: Execution time exceeded {_MAX_EXECUTION_SECONDS // 60} minutes. Failing.")
        sys.exit(1)


def get_access_token(
    storage: Storage,
    force: bool = False,
    allow_device_flow: bool = False,
) -> str | None:
    """Get access token with full authentication strategy.

    Resolution order:
    1. Cached token from storage (unless force=True)
    2. GH_TOKEN environment variable (type-aware routing)
    3. GitHub CLI token (gh auth token)
    4. Device flow (if allow_device_flow=True and OAUTH_CLIENT_ID is set)

    Args:
        storage: Storage instance
        force: Force re-authentication (ignore cached token)
        allow_device_flow: Whether to allow interactive device flow fallback

    Returns:
        Access token string for httpx, or None to use gh CLI api fallback

    Raises:
        SystemExit: If no authentication method succeeds
    """
    # 1. Check cached token
    if not force:
        stored = storage.load_token()
        if stored:
            token_type = get_token_type(stored.access_token)
            print(f"Using cached token (type: {token_type}, created: {stored.created_at})")
            if token_type == "pat":
                print("  Warning: cached token is a PAT, which may be rejected by Copilot API")
            return stored.access_token

    # 2. Check GH_TOKEN environment variable
    env_token = get_token_from_env()
    if env_token:
        token_type = get_token_type(env_token)

        if token_type == "oauth":
            print("Using OAuth token from GH_TOKEN")
            print("  Token source: environment variable (gho_)")
            print("  Model access: FULL (35+ models)")
            # Save to storage for reuse
            _save_token_to_storage(storage, env_token)
            return env_token

        if token_type == "app":
            print("Using GitHub App token from GH_TOKEN")
            print("  Token source: environment variable (ghs_)")
            print("  Model access: FULL (35+ models)")
            _save_token_to_storage(storage, env_token)
            return env_token

        if token_type == "pat":
            print("Personal Access Token (PAT) detected in GH_TOKEN")
            print("  PATs (ghp_*) are explicitly rejected by the Copilot /models endpoint.")

            if allow_device_flow and is_device_flow_available():
                print("  Attempting interactive device flow...")
                try:
                    token = run_device_flow()
                    _save_token_to_storage(storage, token)
                    return token
                except DeviceFlowError as e:
                    print(f"  Device flow failed: {e}")
                    _handle_auth_failure(
                        allow_device_flow=allow_device_flow,
                        reason=f"Device flow failed: {e}",
                    )
            elif allow_device_flow:
                print("  Device flow is not configured (OAUTH_CLIENT_ID missing).")
                print("  Please set OAUTH_CLIENT_ID secret to enable device flow.")

            # Try gh CLI fallback as last resort (will likely fail with PAT too)
            print("  Falling back to gh api command (may also fail with PAT)...")
            return None

        # Unknown token type - try using it directly
        print("Unknown token type in GH_TOKEN, attempting direct use...")
        _save_token_to_storage(storage, env_token)
        return env_token

    # 3. Try GitHub CLI
    gh_available, gh_message = check_gh_auth()
    if gh_available:
        try:
            token = get_gh_token()
            token_type = get_token_type(token)
            if token_type == "pat":
                print("GitHub CLI returned a PAT, which is rejected by Copilot API")
                if allow_device_flow and is_device_flow_available():
                    print("Attempting device flow instead...")
                    try:
                        token = run_device_flow()
                        _save_token_to_storage(storage, token)
                        return token
                    except DeviceFlowError as e:
                        print(f"Device flow failed: {e}")
                        _handle_auth_failure(
                            allow_device_flow=allow_device_flow,
                            reason=f"Device flow failed: {e}",
                        )
            else:
                print("Using GitHub CLI (gh) authentication")
                print(f"  Token type: {token_type}")
                print("  Accessing full Copilot model list (35+ models)")
                _save_token_to_storage(storage, token)
                return token
        except GitHubCLIError:
            pass  # Fall through to device flow or error

    # 4. Device flow as last resort
    if allow_device_flow and is_device_flow_available():
        try:
            token = run_device_flow()
            _save_token_to_storage(storage, token)
            return token
        except DeviceFlowError as e:
            print(f"Device flow failed: {e}")
            _handle_auth_failure(
                allow_device_flow=allow_device_flow,
                reason=f"Device flow failed: {e}",
            )

    # No authentication method succeeded
    _handle_auth_failure(
        allow_device_flow=allow_device_flow,
        reason="No valid authentication method available",
    )
    return None  # Never reached, _handle_auth_failure exits


def _save_token_to_storage(storage: Storage, token: str) -> None:
    """Save a token to local storage."""
    stored_token = StoredToken(
        access_token=token,
        token_type="bearer",
        scope="",
        created_at=datetime.now().isoformat(),
    )
    storage.save_token(stored_token)


def _handle_auth_failure(*, allow_device_flow: bool, reason: str) -> None:
    """Handle authentication failure, optionally creating a notification issue.

    Args:
        allow_device_flow: Whether device flow was attempted (manual trigger)
        reason: Failure reason for the issue body
    """
    print(f"\nAuthentication failed: {reason}")

    if not allow_device_flow:
        # Scheduled trigger - create notification issue
        print("\nThis is a scheduled run. Creating notification issue...")
        create_notification_issue(reason)

    print("\nSolutions:")
    if not allow_device_flow:
        print("  1. Trigger workflow manually (workflow_dispatch) to use device flow")
    print("  2. Set GH_TOKEN to an OAuth token (gho_*) from 'gh auth login'")
    print("  3. Run locally with: gh auth login && python -m copilot_fetcher fetch")
    print("  4. Use local scheduling (cron, systemd, launchd)")

    sys.exit(1)


def create_notification_issue(reason: str) -> None:
    """Create a GitHub issue to notify the repository owner.

    Uses gh CLI to create an issue when token authentication fails
    on a scheduled run.

    Args:
        reason: The failure reason to include in the issue body
    """
    repo = os.environ.get("GITHUB_REPOSITORY")
    actor = os.environ.get("GITHUB_ACTOR", "repository owner")

    if not repo:
        print("  Warning: GITHUB_REPOSITORY not set, cannot create issue")
        return

    title = "[Scheduled] Copilot model fetch failed - token expired/invalid"
    body = (
        f"@{actor}\n\n"
        f"The scheduled GitHub Actions workflow failed to fetch Copilot models.\n\n"
        f"**Reason:** {reason}\n\n"
        f"**What you need to do:**\n"
        f"1. Go to Actions → 'Daily Copilot Models Fetch'\n"
        f"2. Click 'Run workflow' to trigger manually\n"
        f"3. Open the workflow run logs\n"
        f"4. Follow the device flow instructions (link + code)\n"
        f"5. After authorization, the token will be cached automatically\n\n"
        f"**Alternative:**\n"
        f"- Set `GH_TOKEN` to a valid OAuth token (gho_*) from `gh auth login`\n"
        f"- Or run locally: `gh auth login && python -m copilot_fetcher fetch`\n\n"
        f"---\n"
        f"_This issue was created automatically by the scheduled workflow._"
    )

    try:
        result = subprocess.run(
            ["gh", "issue", "create", "--repo", repo, "--title", title, "--body", body],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            print(f"  Created notification issue: {result.stdout.strip()}")
        else:
            print(f"  Warning: Failed to create issue: {result.stderr.strip()}")
    except FileNotFoundError:
        print("  Warning: gh CLI not found, cannot create notification issue")
    except subprocess.TimeoutExpired:
        print("  Warning: Timeout creating notification issue")
    except Exception as e:
        print(f"  Warning: Error creating notification issue: {e}")


def fetch_models(access_token: str | None, storage: Storage) -> None:
    """Fetch and save Copilot models with retry logic.

    Args:
        access_token: OAuth access token or None to use gh CLI api
        storage: Storage instance
    """
    print("\nFetching Copilot models...")

    failures = 0
    while failures < _MAX_TOKEN_FAILURES:
        _check_timeout()

        try:
            with CopilotClient(access_token) as client:
                response = client.get_models()
            break  # Success
        except CopilotAPIError as e:
            failures += 1
            error_msg = str(e)
            print(f"Attempt {failures}/{_MAX_TOKEN_FAILURES} failed: {error_msg}")

            if failures >= _MAX_TOKEN_FAILURES:
                print(f"\nFailed after {_MAX_TOKEN_FAILURES} attempts.")
                sys.exit(1)

            # If token-related error, try to re-authenticate
            if "not accepted" in error_msg.lower() or "not supported" in error_msg.lower():
                print("Token rejected by Copilot API. Trying to re-authenticate...")
                # For now, just retry. In a future enhancement, we could
                # trigger device flow again here for manual triggers.
                time.sleep(2)
            else:
                # Non-token error, fail immediately
                print(f"Non-recoverable error: {error_msg}")
                sys.exit(1)

    # Save to storage
    storage.save_models(response)

    print(f"Fetched {response.total} models")
    print(f"Saved to: {storage.models_file}")


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
        print(f"\n[{family}]")
        for model in sorted(models_by_family[family], key=lambda m: m.get("id", "")):
            model_id = model.get("id", "unknown")
            name = model.get("name", model_id)
            print(f"  - {model_id}")
            if name != model_id:
                print(f"    ({name})")

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
        print("No models found. Run 'copilot-fetcher fetch' first.")
        sys.exit(1)

    print(json.dumps(raw, indent=2, ensure_ascii=False))


def show_auth_status() -> None:
    """Show authentication status."""
    print("\nAuthentication Status")
    print("=" * 60)

    # Check GH_TOKEN env
    env_token = get_token_from_env()
    if env_token:
        token_type = get_token_type(env_token)
        print(f"GH_TOKEN: set (type: {token_type})")
        if token_type == "pat":
            print("  Warning: PAT will be rejected by Copilot API")
    else:
        print("GH_TOKEN: not set")

    # Check gh CLI
    gh_available, gh_message = check_gh_auth()
    if gh_available:
        print(f"GitHub CLI: {gh_message}")
    else:
        print(f"GitHub CLI: {gh_message}")

    # Check device flow
    if is_device_flow_available():
        print("Device Flow: available (OAUTH_CLIENT_ID set)")
    else:
        print("Device Flow: not configured (OAUTH_CLIENT_ID missing)")

    print("\n" + "=" * 60)


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        prog="copilot-fetcher",
        description="Fetch GitHub Copilot models via GitHub CLI",
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
        help="Authenticate with GitHub CLI",
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

    # TUI command
    subparsers.add_parser(
        "tui",
        help="Launch interactive TUI mode",
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

    # Determine if device flow should be allowed based on trigger type
    event_name = os.environ.get("GITHUB_EVENT_NAME", "")
    allow_device_flow = event_name == "workflow_dispatch"

    if args.command == "auth":
        get_access_token(storage, force=args.force, allow_device_flow=True)

    elif args.command == "fetch":
        access_token = get_access_token(
            storage, force=args.force_auth, allow_device_flow=allow_device_flow
        )
        fetch_models(access_token, storage)

    elif args.command == "list":
        list_models(storage)

    elif args.command == "raw":
        show_raw(storage)

    elif args.command == "status":
        show_auth_status()

    elif args.command == "tui":
        from copilot_fetcher.tui import main as tui_main

        tui_main()

    elif args.command == "clear":
        storage.delete_token()
        if storage.models_file.exists():
            storage.models_file.unlink()
        print("Cleared all stored data")

    return 0


if __name__ == "__main__":
    sys.exit(main())
