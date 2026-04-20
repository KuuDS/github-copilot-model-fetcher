"""GitHub OAuth Device Flow implementation (RFC 8628).

Provides interactive authentication for headless environments like GitHub Actions.
User scans a URL + enters a code to authorize the application.
"""

from __future__ import annotations

import os
import subprocess
import time
from typing import Any

import httpx


class DeviceFlowError(Exception):
    """Device flow authentication error."""

    pass


def start_device_flow(client_id: str, scope: str = "repo read:user") -> dict[str, Any]:
    """Start GitHub OAuth device flow.

    Posts to /login/device/code to obtain a device code and user verification
    URL that the user opens in a browser.

    Args:
        client_id: OAuth App Client ID
        scope: Space-separated OAuth scopes to request

    Returns:
        Dict with keys: device_code, user_code, verification_uri,
        verification_uri_complete, expires_in, interval

    Raises:
        DeviceFlowError: If the request fails
    """
    try:
        response = httpx.post(
            "https://github.com/login/device/code",
            headers={"Accept": "application/json"},
            data={
                "client_id": client_id,
                "scope": scope,
            },
            timeout=30.0,
        )
        response.raise_for_status()
        data = response.json()

        if "error" in data:
            raise DeviceFlowError(f"Device flow start failed: {data['error']}")

        return data
    except httpx.HTTPStatusError as e:
        raise DeviceFlowError(f"HTTP error starting device flow: {e}") from e
    except httpx.RequestError as e:
        raise DeviceFlowError(f"Network error starting device flow: {e}") from e


def poll_for_token(
    client_id: str,
    device_code: str,
    interval: int,
    timeout: int = 300,
) -> str:
    """Poll GitHub for access token after user authorizes.

    Blocks until the user completes authorization in the browser or timeout.

    Args:
        client_id: OAuth App Client ID
        device_code: Device code from start_device_flow
        interval: Polling interval in seconds
        timeout: Total timeout in seconds (default 300 = 5 minutes)

    Returns:
        OAuth access token (gho_ prefix)

    Raises:
        DeviceFlowError: On timeout, denial, or other flow errors
    """
    start_time = time.time()
    current_interval = interval

    print(f"\nWaiting for authorization (timeout: {timeout}s)...")
    print("If you don't complete authorization in time, the workflow will fail.\n")

    while time.time() - start_time < timeout:
        time.sleep(current_interval)

        try:
            response = httpx.post(
                "https://github.com/login/oauth/access_token",
                headers={"Accept": "application/json"},
                data={
                    "client_id": client_id,
                    "device_code": device_code,
                    "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                },
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()

            if "access_token" in data:
                return data["access_token"]

            error = data.get("error")
            if error == "authorization_pending":
                # User hasn't completed authorization yet, keep polling
                elapsed = int(time.time() - start_time)
                remaining = timeout - elapsed
                print(f"  Waiting... ({elapsed}s elapsed, {remaining}s remaining)")
                continue
            elif error == "slow_down":
                # Server asks us to slow down
                current_interval += 5
                print(f"  Server asked to slow down, interval increased to {current_interval}s")
                continue
            elif error == "expired_token":
                raise DeviceFlowError(
                    "Device code expired. The authorization window closed before completion."
                )
            elif error == "access_denied":
                raise DeviceFlowError(
                    "Authorization denied. You declined the authorization request."
                )
            else:
                raise DeviceFlowError(f"Device flow error: {error}")

        except httpx.HTTPStatusError as e:
            raise DeviceFlowError(f"HTTP error polling for token: {e}") from e
        except httpx.RequestError as e:
            raise DeviceFlowError(f"Network error polling for token: {e}") from e

    raise DeviceFlowError(
        f"Authorization timeout ({timeout}s). "
        "Please trigger the workflow manually again when you are ready to scan."
    )


def update_repo_secret(token: str, secret_name: str = "GH_TOKEN") -> None:
    """Update a repository secret via GitHub CLI.

    Uses 'gh secret set' which encrypts the value server-side.

    Args:
        token: The secret value to store
        secret_name: Name of the secret to update

    Raises:
        DeviceFlowError: If the update fails
    """
    repo = os.environ.get("GITHUB_REPOSITORY")
    if not repo:
        raise DeviceFlowError(
            "GITHUB_REPOSITORY not set. Cannot update secret outside of GitHub Actions."
        )

    try:
        result = subprocess.run(
            ["gh", "secret", "set", secret_name, "--body", token, "--repo", repo],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            raise DeviceFlowError(f"gh secret set failed: {result.stderr.strip()}")
    except FileNotFoundError:
        raise DeviceFlowError(
            "gh CLI not found. Cannot update repository secret."
        )
    except subprocess.TimeoutExpired:
        raise DeviceFlowError("Timeout updating repository secret")


def is_device_flow_available() -> bool:
    """Check if device flow can be attempted.

    Returns:
        True if OAUTH_CLIENT_ID environment variable is set
    """
    return bool(os.environ.get("OAUTH_CLIENT_ID"))


def run_device_flow() -> str:
    """Run the complete device flow and return the access token.

    Also updates the GH_TOKEN repository secret with the new token.

    Returns:
        OAuth access token string

    Raises:
        DeviceFlowError: If any step fails
    """
    client_id = os.environ.get("OAUTH_CLIENT_ID")
    if not client_id:
        raise DeviceFlowError(
            "OAUTH_CLIENT_ID not set.\n"
            "To use device flow in GitHub Actions:\n"
            "1. Create an OAuth App: GitHub Settings → Developer settings → OAuth Apps\n"
            "2. Copy the Client ID\n"
            "3. Add it as a repository secret named OAUTH_CLIENT_ID"
        )

    print("=" * 70)
    print("GitHub OAuth Device Flow")
    print("=" * 70)
    print()
    print("No valid OAuth token found. Starting interactive device flow...")
    print()

    flow_data = start_device_flow(client_id)
    user_code = flow_data["user_code"]
    verification_uri = flow_data["verification_uri"]
    verification_uri_complete = flow_data.get("verification_uri_complete")
    device_code = flow_data["device_code"]
    interval = flow_data.get("interval", 5)

    print("Please authorize this application:")
    print()
    print("  1. Open this link in your browser:")
    if verification_uri_complete:
        print(f"     {verification_uri_complete}")
    else:
        print(f"     {verification_uri}")
    print()
    print(f"  2. Enter this code: {user_code}")
    print()
    print("  (If the link above doesn't work, go to the URL and enter the code manually)")
    print()

    access_token = poll_for_token(client_id, device_code, interval)

    print("\nAuthorization successful!")
    print("Updating repository secret with new token...")
    update_repo_secret(access_token)
    print("Token cached. Next run will use the cached token automatically.")
    print()

    return access_token
