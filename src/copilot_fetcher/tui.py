"""Copilot TUI (Text User Interface) - Interactive mode.

A Python implementation of GitHub Copilot CLI's interactive interface.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from typing import Any

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.shortcuts import clear
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.text import Text

from copilot_fetcher.api import CopilotAPIError, CopilotClient
from copilot_fetcher.gh_auth import get_gh_token


console = Console()


@dataclass
class ChatMessage:
    """A chat message."""

    role: str  # "user", "assistant", "system"
    content: str
    model: str | None = None
    timestamp: str = field(default_factory=lambda: "")


class CopilotTUI:
    """Copilot Text User Interface."""

    def __init__(self) -> None:
        """Initialize the TUI."""
        self.console = Console()
        self.session = PromptSession()
        self.messages: list[ChatMessage] = []
        self.current_model = "gpt-4o"
        self.client: CopilotClient | None = None
        self.running = True

        # Key bindings
        self.kb = KeyBindings()
        self._setup_key_bindings()

        # Commands
        self.commands = {
            "/help": self._show_help,
            "/models": self._show_models,
            "/model": self._switch_model,
            "/clear": self._clear_chat,
            "/history": self._show_history,
            "/exit": self._exit,
            "/quit": self._exit,
        }

    def _setup_key_bindings(self) -> None:
        """Setup keyboard shortcuts."""

        @self.kb.add("c-c")
        @self.kb.add("c-d")
        def _(event):
            """Ctrl+C or Ctrl+D to exit."""
            self.running = False
            event.app.exit()

        @self.kb.add("c-l")
        def _(event):
            """Ctrl+L to clear screen."""
            clear()
            self._show_header()

    def _show_header(self) -> None:
        """Display the application header."""
        header = Text()
        header.append("╭─────────────────────────────────────────────────────╮\n", style="blue")
        header.append("│  ", style="blue")
        header.append("GitHub Copilot TUI", style="bold cyan")
        header.append("  -  Interactive Model Explorer" + " " * 15, style="cyan")
        header.append("│\n", style="blue")
        header.append("╰─────────────────────────────────────────────────────╯", style="blue")
        self.console.print(header)
        self.console.print()

    def _show_welcome(self) -> None:
        """Display welcome message."""
        welcome = Panel(
            "[bold cyan]Welcome to Copilot TUI![/bold cyan]\n\n"
            "This is an interactive interface for exploring GitHub Copilot.\n"
            "Type [bold green]/help[/bold green] for available commands or start chatting.\n\n"
            f"Current model: [bold yellow]{self.current_model}[/bold yellow]",
            title="👋 Welcome",
            border_style="cyan",
        )
        self.console.print(welcome)
        self.console.print()

    def _show_help(self, args: str = "") -> None:
        """Display help information."""
        help_table = Table(title="Available Commands", show_header=True)
        help_table.add_column("Command", style="cyan", no_wrap=True)
        help_table.add_column("Description", style="white")
        help_table.add_column("Example", style="dim")

        help_table.add_row("/help", "Show this help message", "/help")
        help_table.add_row("/models", "List available models", "/models")
        help_table.add_row("/model", "Switch to a different model", "/model gpt-4o")
        help_table.add_row("/clear", "Clear chat history", "/clear")
        help_table.add_row("/history", "Show conversation history", "/history")
        help_table.add_row("/exit, /quit", "Exit the application", "/exit")
        help_table.add_row("Ctrl+C, Ctrl+D", "Exit the application", "")
        help_table.add_row("Ctrl+L", "Clear screen", "")

        self.console.print(help_table)
        self.console.print()

        tips = Panel(
            "[bold]Tips:[/bold]\n"
            "• Use [cyan]Tab[/cyan] for command completion\n"
            "• Use [cyan]↑/↓[/cyan] arrow keys to navigate history\n"
            "• Models with [green]✓[/green] are available for selection",
            title="💡 Tips",
            border_style="dim",
        )
        self.console.print(tips)
        self.console.print()

    def _show_models(self, args: str = "") -> None:
        """Display available models."""
        if not self.client:
            self.console.print("[red]Error: Not authenticated. Run 'gh auth login' first.[/red]")
            return

        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console,
                transient=True,
            ) as progress:
                progress.add_task(description="Fetching models...", total=None)
                response = self.client.get_models()

            # Group by provider
            models_by_provider: dict[str, list[str]] = {}
            for model in response.models:
                provider = "Unknown"
                model_id = model.id.lower()
                if "claude" in model_id:
                    provider = "Anthropic"
                elif "gpt" in model_id or "codex" in model_id:
                    provider = "OpenAI"
                elif "gemini" in model_id:
                    provider = "Google"
                elif "grok" in model_id:
                    provider = "xAI"
                elif "embedding" in model_id:
                    provider = "Embedding"

                if provider not in models_by_provider:
                    models_by_provider[provider] = []
                models_by_provider[provider].append(model.id)

            # Display table
            table = Table(title=f"Available Models ({response.total} total)", show_header=True)
            table.add_column("Provider", style="cyan", no_wrap=True)
            table.add_column("Models", style="white")
            table.add_column("Status", style="green", justify="center")

            for provider in sorted(models_by_provider.keys()):
                models = models_by_provider[provider]
                model_list = ", ".join(sorted(models)[:5])
                if len(models) > 5:
                    model_list += f" (+{len(models) - 5} more)"

                status = "✓" if self.current_model in models else ""
                table.add_row(provider, model_list, status)

            self.console.print(table)
            self.console.print()
            self.console.print(f"[dim]Current model: [cyan]{self.current_model}[/cyan][/dim]")
            self.console.print()

        except CopilotAPIError as e:
            self.console.print(f"[red]Error fetching models: {e}[/red]")

    def _switch_model(self, args: str = "") -> None:
        """Switch to a different model."""
        if not args.strip():
            self.console.print("[yellow]Usage: /model <model-id>[/yellow]")
            self.console.print("[dim]Example: /model claude-sonnet-4.5[/dim]")
            return

        model_id = args.strip()
        old_model = self.current_model
        self.current_model = model_id
        self.console.print(
            f"[green]✓[/green] Switched model: [dim]{old_model}[/dim] → [cyan]{model_id}[/cyan]"
        )
        self.console.print()

    def _clear_chat(self, args: str = "") -> None:
        """Clear chat history."""
        self.messages.clear()
        clear()
        self._show_header()
        self.console.print("[dim]Chat history cleared.[/dim]")
        self.console.print()

    def _show_history(self, args: str = "") -> None:
        """Display conversation history."""
        if not self.messages:
            self.console.print("[dim]No conversation history.[/dim]")
            return

        for msg in self.messages[-10:]:  # Show last 10 messages
            if msg.role == "user":
                self.console.print(f"[bold cyan]You:[/bold cyan] {msg.content}")
            elif msg.role == "assistant":
                self.console.print(f"[bold green]Copilot:[/bold green] {msg.content}")
            self.console.print()

    def _exit(self, args: str = "") -> None:
        """Exit the application."""
        self.console.print("[dim]Goodbye! 👋[/dim]")
        self.running = False
        sys.exit(0)

    def _process_command(self, user_input: str) -> bool:
        """Process a command. Returns True if command was handled."""
        user_input = user_input.strip()

        if not user_input.startswith("/"):
            return False

        # Parse command and arguments
        parts = user_input.split(maxsplit=1)
        command = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""

        if command in self.commands:
            self.commands[command](args)
            return True
        else:
            self.console.print(f"[red]Unknown command: {command}[/red]")
            self.console.print("[dim]Type /help for available commands.[/dim]")
            return True

    def _handle_chat(self, user_input: str) -> None:
        """Handle chat message (placeholder for actual AI integration)."""
        # Add user message
        self.messages.append(ChatMessage(role="user", content=user_input))

        # In a real implementation, this would call the Copilot API
        # For now, we'll show a placeholder response
        self.console.print()
        response_text = (
            f"[bold green]Copilot[/bold green] ([dim]{self.current_model}[/dim]):\n"
            "I'm a TUI demo for exploring Copilot models.\n"
            "To see available models, type [cyan]/models[/cyan].\n"
            "To switch models, type [cyan]/model <model-id>[/cyan]."
        )
        self.console.print(response_text)
        self.console.print()

        # Add assistant message
        self.messages.append(
            ChatMessage(role="assistant", content=response_text, model=self.current_model)
        )

    def run(self) -> None:
        """Run the TUI."""
        clear()
        self._show_header()
        self._show_welcome()

        # Authenticate
        try:
            token = get_gh_token()
            self.client = CopilotClient(token)
            self.console.print("[green]✓[/green] Authenticated with GitHub Copilot")
            self.console.print()
        except Exception as e:
            self.console.print(f"[yellow]⚠ Warning: {e}[/yellow]")
            self.console.print(
                "[dim]Some features may be limited. Run 'gh auth login' to authenticate.[/dim]"
            )
            self.console.print()

        # Main loop
        while self.running:
            try:
                # Get user input
                user_input = self.session.prompt(
                    "[cyan]copilot[/cyan] [dim]>>[/dim] ",
                    key_bindings=self.kb,
                )

                if not user_input.strip():
                    continue

                # Process command or chat
                if not self._process_command(user_input):
                    self._handle_chat(user_input)

            except (EOFError, KeyboardInterrupt):
                self._exit()
                break
            except Exception as e:
                self.console.print(f"[red]Error: {e}[/red]")


def main() -> None:
    """Entry point for TUI."""
    try:
        tui = CopilotTUI()
        tui.run()
    except Exception as e:
        console.print(f"[red]Fatal error: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()
