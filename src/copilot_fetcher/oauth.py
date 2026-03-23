"""OAuth 2.0 Device Flow authentication for GitHub Copilot API."""

from __future__ import annotations

import time
import webbrowser
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlencode

import httpx


@dataclass
class DeviceCodeResponse:
    """Response from device code endpoint."""

    device_code: str
    user_code: str
    verification_uri: str
    expires_in: int
    interval: int


@dataclass
class TokenResponse:
    """Response from token endpoint."""

    access_token: str
    token_type: str
    scope: str


class GitHubOAuthError(Exception):
    """OAuth authentication error."""

    pass


class GitHubDeviceFlow:
    """GitHub OAuth 2.0 Device Authorization Grant implementation."""

    DEVICE_CODE_URL = "https://github.com/login/device/code"
    TOKEN_URL = "https://github.com/login/oauth/access_token"

    def __init__(self, client_id: str) -> None:
        """Initialize with OAuth App client ID.

        Args:
            client_id: GitHub OAuth App client ID
        """
        self.client_id = client_id

    def request_device_code(self, scope: str = "read:user") -> DeviceCodeResponse:
        """Request device and user verification codes.

        Args:
            scope: OAuth scopes (default: read:user)

        Returns:
            DeviceCodeResponse with codes and verification URI

        Raises:
            GitHubOAuthError: If request fails
        """
        data = {
            "client_id": self.client_id,
            "scope": scope,
        }

        try:
            response = httpx.post(
                self.DEVICE_CODE_URL,
                data=data,
                headers={"Accept": "application/json"},
                timeout=30.0,
            )
            response.raise_for_status()
            result = response.json()

            if "error" in result:
                raise GitHubOAuthError(f"Device code request failed: {result['error']}")

            return DeviceCodeResponse(
                device_code=result["device_code"],
                user_code=result["user_code"],
                verification_uri=result["verification_uri"],
                expires_in=result["expires_in"],
                interval=result.get("interval", 5),
            )
        except httpx.HTTPStatusError as e:
            raise GitHubOAuthError(f"HTTP error requesting device code: {e}") from e
        except httpx.RequestError as e:
            raise GitHubOAuthError(f"Network error requesting device code: {e}") from e

    def poll_for_token(
        self,
        device_code: str,
        interval: int = 5,
        max_attempts: int = 60,
    ) -> TokenResponse:
        """Poll token endpoint until user authorizes or timeout.

        Args:
            device_code: Device code from request_device_code
            interval: Polling interval in seconds
            max_attempts: Maximum polling attempts

        Returns:
            TokenResponse with access token

        Raises:
            GitHubOAuthError: If polling fails or times out
        """
        data = {
            "client_id": self.client_id,
            "device_code": device_code,
            "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
        }

        for attempt in range(max_attempts):
            time.sleep(interval)

            try:
                response = httpx.post(
                    self.TOKEN_URL,
                    data=data,
                    headers={"Accept": "application/json"},
                    timeout=30.0,
                )
                response.raise_for_status()
                result = response.json()

                if "access_token" in result:
                    return TokenResponse(
                        access_token=result["access_token"],
                        token_type=result.get("token_type", "bearer"),
                        scope=result.get("scope", ""),
                    )

                error = result.get("error")

                if error == "authorization_pending":
                    # User hasn't entered code yet, continue polling
                    continue
                elif error == "slow_down":
                    # Server requests slower polling
                    interval += 5
                    continue
                elif error == "expired_token":
                    raise GitHubOAuthError("Device code expired. Please restart authentication.")
                elif error == "access_denied":
                    raise GitHubOAuthError("User denied authorization.")
                elif error:
                    raise GitHubOAuthError(f"Token request failed: {error}")

            except httpx.HTTPStatusError as e:
                raise GitHubOAuthError(f"HTTP error polling for token: {e}") from e
            except httpx.RequestError as e:
                raise GitHubOAuthError(f"Network error polling for token: {e}") from e

        raise GitHubOAuthError(
            f"Polling timeout after {max_attempts} attempts. Please restart authentication."
        )

    def authenticate(
        self,
        scope: str = "read:user",
        open_browser: bool = True,
    ) -> TokenResponse:
        """Complete OAuth device flow authentication.

        Args:
            scope: OAuth scopes
            open_browser: Whether to open browser automatically

        Returns:
            TokenResponse with access token
        """
        # Step 1: Request device code
        device_response = self.request_device_code(scope)

        print(f"\n{'=' * 60}")
        print("GitHub OAuth Device Flow")
        print(f"{'=' * 60}")
        print(f"\nPlease visit: {device_response.verification_uri}")
        print(f"And enter code: {device_response.user_code}")
        print(f"\nThis code will expire in {device_response.expires_in} seconds")
        print(f"{'=' * 60}\n")

        if open_browser:
            try:
                webbrowser.open(device_response.verification_uri)
                print("Browser opened automatically.\n")
            except Exception:
                print("Could not open browser automatically.\n")

        # Step 2: Poll for token
        print("Waiting for authorization...")
        return self.poll_for_token(
            device_response.device_code,
            device_response.interval,
        )


def get_access_token(client_id: str, open_browser: bool = True) -> str:
    """Convenience function to get access token.

    Args:
        client_id: GitHub OAuth App client ID
        open_browser: Whether to open browser automatically

    Returns:
        Access token string
    """
    flow = GitHubDeviceFlow(client_id)
    token_response = flow.authenticate(open_browser=open_browser)
    return token_response.access_token
