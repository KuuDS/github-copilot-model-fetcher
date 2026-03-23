"""GitHub Copilot CLI wrapper for interactive operations.

This module provides Python bindings to interact with the `gh copilot` CLI,
enabling programmatic access to Copilot features.
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from typing import Any


class CopilotCLIError(Exception):
    """Error running gh copilot CLI."""

    pass


@dataclass
class CopilotSuggestion:
    """A Copilot code suggestion."""

    text: str
    explanation: str | None = None


@dataclass
class CopilotExplanation:
    """A Copilot explanation response."""

    text: str
    code_blocks: list[str] | None = None


class CopilotCLI:
    """Wrapper for the `gh copilot` CLI command."""

    def __init__(self) -> None:
        """Initialize Copilot CLI wrapper."""
        self._check_cli()

    def _check_cli(self) -> None:
        """Check if gh copilot CLI is available."""
        try:
            result = subprocess.run(
                ["gh", "copilot", "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode != 0:
                raise CopilotCLIError("gh copilot CLI not available")
        except FileNotFoundError:
            raise CopilotCLIError("gh CLI not found. Install from: https://cli.github.com/")

    def suggest(
        self,
        prompt: str,
        language: str | None = None,
        target: str | None = None,
        auto: bool = False,
    ) -> CopilotSuggestion:
        """Get code suggestions from Copilot.

        Args:
            prompt: The coding task or question
            language: Target programming language
            target: Target file or directory
            auto: Allow all tools to run automatically

        Returns:
            CopilotSuggestion with code and explanation
        """
        cmd = ["gh", "copilot", "suggest"]

        if language:
            cmd.extend(["--language", language])
        if target:
            cmd.extend(["--target", target])
        if auto:
            cmd.append("--auto")

        cmd.append(prompt)

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode != 0:
                raise CopilotCLIError(f"Copilot suggest failed: {result.stderr}")

            return CopilotSuggestion(
                text=result.stdout,
                explanation=None,  # Could parse from output
            )
        except subprocess.TimeoutExpired:
            raise CopilotCLIError("Copilot suggest timed out")

    def explain(
        self,
        code: str,
        target: str | None = None,
        auto: bool = False,
    ) -> CopilotExplanation:
        """Get explanation of code from Copilot.

        Args:
            code: The code to explain
            target: Target file or directory
            auto: Allow all tools to run automatically

        Returns:
            CopilotExplanation with explanation text
        """
        cmd = ["gh", "copilot", "explain"]

        if target:
            cmd.extend(["--target", target])
        if auto:
            cmd.append("--auto")

        cmd.append(code)

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode != 0:
                raise CopilotCLIError(f"Copilot explain failed: {result.stderr}")

            return CopilotExplanation(
                text=result.stdout,
                code_blocks=None,  # Could parse from output
            )
        except subprocess.TimeoutExpired:
            raise CopilotCLIError("Copilot explain timed out")

    def prompt(
        self,
        message: str,
        model: str | None = None,
        auto: bool = False,
    ) -> str:
        """Send a prompt to Copilot chat.

        This uses the `gh copilot -p` flag for non-interactive prompts.

        Args:
            message: The prompt message
            model: Model to use (e.g., "gpt-4", "claude-sonnet-4.5")
            auto: Allow all tools to run automatically

        Returns:
            Copilot's response text
        """
        cmd = ["gh", "copilot", "-p", message]

        if model:
            cmd.extend(["--model", model])
        if auto:
            cmd.append("--auto")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,
            )

            if result.returncode != 0:
                raise CopilotCLIError(f"Copilot prompt failed: {result.stderr}")

            return result.stdout
        except subprocess.TimeoutExpired:
            raise CopilotCLIError("Copilot prompt timed out")

    def get_models_via_cli(self) -> list[dict[str, Any]]:
        """Try to get models using gh CLI.

        Note: This is an experimental approach using gh CLI internals.
        May not work in all environments.

        Returns:
            List of model information dictionaries
        """
        # Try to get models using gh api command
        # This may not work if gh doesn't expose this endpoint
        try:
            result = subprocess.run(
                ["gh", "api", "/copilot/models"],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0:
                data = json.loads(result.stdout)
                return data.get("data", [])
        except (subprocess.TimeoutExpired, json.JSONDecodeError):
            pass

        # Fallback: return empty list
        return []

    def is_authenticated(self) -> bool:
        """Check if Copilot CLI is authenticated.

        Returns:
            True if authenticated, False otherwise
        """
        try:
            result = subprocess.run(
                ["gh", "auth", "status"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return result.returncode == 0
        except Exception:
            return False


def run_copilot_interactive() -> None:
    """Run gh copilot in interactive mode using Python.

    This launches the actual gh copilot TUI.
    """
    import os
    import sys

    try:
        # Replace current process with gh copilot
        os.execvp("gh", ["gh", "copilot"])
    except FileNotFoundError:
        print("Error: gh CLI not found. Install from https://cli.github.com/")
        sys.exit(1)
    except Exception as e:
        print(f"Error launching gh copilot: {e}")
        sys.exit(1)
