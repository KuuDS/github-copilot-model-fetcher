# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Python CLI tool that fetches available GitHub Copilot models via the `api.githubcopilot.com/models` endpoint. Supports GitHub CLI authentication (`gh auth login`) or `GH_TOKEN` environment variable. Data is stored locally in `~/.copilot-fetcher/`.

## Common Commands

Install dependencies (uses `uv` or `pip`):
```bash
uv pip install -e ".[dev]"
# or: pip install -e ".[dev]"
```

Run linting and formatting (configured in `pyproject.toml`):
```bash
ruff check .
ruff format .
```

Run tests:
```bash
pytest
```

Run the application (via wrapper script that activates venv):
```bash
./run.sh fetch    # Fetch and save models
./run.sh list     # Display grouped model list
./run.sh status   # Check auth status
./run.sh tui      # Launch interactive TUI
./run.sh raw      # Show raw JSON
```

Or run directly with Python:
```bash
python -m copilot_fetcher <command>
```

## Architecture

### Authentication Strategy (Dual Path)

`copilot_fetcher/gh_auth.py` handles two auth paths:
1. **GitHub CLI token** (`gh auth token`): Preferred for local dev. Token is cached in `~/.copilot-fetcher/token.json`.
2. **GH_TOKEN env var**: For CI/GitHub Actions. When present, `CopilotClient` bypasses `httpx` and delegates to `gh api` command (PAT is not accepted by the Copilot `/models` endpoint).

`copilot_fetcher/api.py` — `CopilotClient` switches transport based on whether `access_token` is provided:
- With token: uses `httpx.Client` with Bearer auth against `https://api.githubcopilot.com`
- Without token: shells out to `gh api https://api.githubcopilot.com/models`

### CLI Entry Point

`copilot_fetcher/__main__.py` defines subcommands via `argparse`:
- `auth`, `fetch`, `list`, `raw`, `status`, `tui`, `clear`
- The `fetch` command resolves auth, calls `CopilotClient.get_models()`, and saves via `Storage`
- The `list` command groups models by family (claude/gpt/gemini/grok) for display

### Storage

`copilot_fetcher/storage.py` — `Storage` class manages JSON files in `~/.copilot-fetcher/`:
- `token.json` — cached OAuth token (chmod 600)
- `models.json` — fetched model list with `fetched_at` timestamp

### TUI

`copilot_fetcher/tui.py` — Interactive terminal UI using `rich` + `prompt_toolkit`. Commands prefixed with `/` (e.g., `/models`, `/model <id>`, `/help`). Chat mode is currently a placeholder (no actual AI integration).

### OpenSpec Workflow

This repo uses OpenSpec for change management. The `openspec/` directory contains `config.yaml` and `changes/`. Use `/opsx:propose`, `/opsx:apply`, `/opsx:archive` for spec-driven development.

## Important Constraints

- **GitHub Actions limitation**: The Copilot `/models` endpoint does not accept Personal Access Tokens. The workflow in `.github/workflows/daily-fetch.yml` gracefully handles failure and documents this. Local scheduling (cron/systemd/launchd) is the recommended automation approach.
- **Requires GitHub CLI**: The `gh` command must be installed and authenticated for most operations.
- **Virtual environment**: Wrapper scripts (`run.sh`, `fetch.sh`) source `set_env.sh` which expects a `.venv` directory in the project root.
