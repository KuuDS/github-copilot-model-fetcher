# GitHub Copilot Model Fetcher

Fetch available GitHub Copilot models via the `api.githubcopilot.com/models` endpoint.

Gets the complete **35+ model list** including Claude, GPT, Gemini, Grok, and more.

## Features

- GitHub CLI authentication (`gh auth login`)
- OAuth device flow for headless environments (GitHub Actions)
- Fetch complete Copilot model list (35+ models)
- Save raw unfiltered API response (all fields preserved)
- Group models by provider for display
- Interactive TUI mode
- Local JSON storage with token caching
- Scheduled runs via GitHub Actions with automatic issue notification on failure

## Installation

```bash
# Clone repository
git clone https://github.com/KuuDS/github-copilot-model-fetcher.git
cd github-copilot-model-fetcher

# Install dependencies
uv pip install -e ".[dev]"
# or: pip install -e ".[dev]"
```

## Prerequisites

Install and configure **GitHub CLI**:

```bash
# Install GitHub CLI
# https://cli.github.com/

# Login (local development)
gh auth login
```

## Usage

### Check authentication status

```bash
./run.sh status
```

### Authenticate (force re-auth)

```bash
./run.sh auth
```

### Fetch model list

```bash
./run.sh fetch
```

Output:
```
Using GitHub CLI (gh) authentication
  Token type: oauth
  Accessing full Copilot model list (35+ models)

Fetching Copilot models...
Fetched 35 models
Saved to: ~/.copilot-fetcher/models.json
```

### List models

```bash
./run.sh list
```

Example output:

```
================================================================================
GitHub Copilot Models (fetched: 2026-04-21T01:54:56)
================================================================================

[Anthropic Claude]
  - claude-opus-4.6
    (Claude Opus 4.6)
  - claude-sonnet-4.6
    (Claude Sonnet 4.6)
  - claude-haiku-4.5
    (Claude Haiku 4.5)
  - ...

[OpenAI GPT]
  - gpt-5.4
    (GPT-5.4)
  - gpt-4.1
    (GPT-4.1)
  - gpt-5.1-codex
    (GPT-5.1-Codex)
  - ...

[Google Gemini]
  - gemini-2.5-pro
    (Gemini 2.5 Pro)

[xAI Grok]
  - grok-code-fast-1
    (Grok Code Fast 1)

================================================================================
Total: 35 models
================================================================================
```

### View raw JSON

```bash
./run.sh raw
```

### Launch TUI mode

```bash
./run.sh tui
```

TUI commands (prefix with `/`):
- `/models` - List all models
- `/model <id>` - Show model details
- `/help` - Show help
- `/quit` - Exit TUI

### Clear stored data

```bash
./run.sh clear
```

## Supported Models

Complete model list available with GitHub CLI authentication:

### Anthropic Claude
- Claude Opus 4.5, 4.6
- Claude Sonnet 4, 4.5, 4.6
- Claude Haiku 4.5

### OpenAI GPT
- GPT-4.1 series
- GPT-5 series (5-mini, 5.1, 5.2, 5.4, etc.)
- GPT-5 Codex series (5.1-codex, 5.2-codex, 5.3-codex, etc.)
- GPT-4o series

### Google Gemini
- Gemini 2.5 Pro

### xAI Grok
- Grok Code Fast 1

### Embedding Models
- text-embedding-3-small
- text-embedding-ada-002

## Storage Location

Default data stored in `~/.copilot-fetcher/`:

- `token.json` - Cached access token (permissions 600)
- `models.json` - Fetched model list with raw API response

## API Reference

### Python API

```python
from copilot_fetcher.api import CopilotClient
from copilot_fetcher.gh_auth import get_gh_token

# Get GitHub CLI token
token = get_gh_token()

# Use client
with CopilotClient(token) as client:
    raw_data = client.get_models_raw()
    print(f"Fetched {len(raw_data['data'])} models")
```

### Modules

- `copilot_fetcher.gh_auth` - GitHub CLI authentication
- `copilot_fetcher.api` - GitHub Copilot API client
- `copilot_fetcher.storage` - Local data storage
- `copilot_fetcher.device_flow` - OAuth device flow (RFC 8628)
- `copilot_fetcher.tui` - Interactive terminal UI

## GitHub Actions Setup

This project supports **interactive OAuth device flow** in GitHub Actions. When manually triggered, it displays a verification link and code in the Actions logs. After authorization, the OAuth token is automatically cached for scheduled runs.

### Authentication Strategy

The code uses GitHub CLI's official OAuth App (`client_id: 178c6fc778ccc68e1d6a`) by default. This grants the same permissions as `gh auth login` (full Copilot model access). **You do NOT need to create your own OAuth App.**

### Required Secrets

| Secret | Required | Description |
|--------|----------|-------------|
| `COPILOT_TOKEN` | Yes (initially spaces) | OAuth token (`gho_*`). Device flow auto-updates this. Initial value can be spaces (trimmed) |
| `GH_PAT` | Yes (for caching) | Personal Access Token with `repo` scope. Only used to authenticate `gh secret set` |

### Setup Steps

1. **Create `GH_PAT` Secret**:
   - Go to https://github.com/settings/tokens/new
   - Select **`repo`** scope
   - Copy the token
   - Add as repository secret: Settings → Secrets and variables → Actions → New repository secret
   - Name: `GH_PAT`

2. **Create `COPILOT_TOKEN` Secret**:
   - Add as repository secret
   - Name: `COPILOT_TOKEN`
   - Value: `   ` (a few spaces — the code trims whitespace)

3. **Trigger Workflow Manually**:
   - Go to Actions → "Daily Copilot Models Fetch" → "Run workflow"
   - Open the workflow run logs
   - You will see a link and a user code — open the link and enter the code
   - After authorization, the OAuth token is automatically saved to `COPILOT_TOKEN`

### Trigger Behavior

| Trigger Type | Device Flow | On Token Failure |
|-------------|-------------|------------------|
| `workflow_dispatch` (manual) | Enabled — shows link + code | Fails immediately |
| `schedule` (cron) | Disabled | Creates issue to notify you |

### Why Not PAT?

The GitHub Copilot API (`api.githubcopilot.com/models`) **explicitly rejects Personal Access Tokens (PATs)** with HTTP 400. Only OAuth tokens (`gho_*` from `gh auth login` or device flow) and GitHub App tokens (`ghs_*`) are accepted.

### Workflow Configuration

The workflow is defined in `.github/workflows/daily-fetch.yml`:

```yaml
name: Daily Copilot Models Fetch

on:
  schedule:
    - cron: '0 0 * * *'  # Daily at 00:00 UTC
  workflow_dispatch:     # Allow manual trigger (enables device flow)

jobs:
  fetch-models:
    runs-on: ubuntu-latest
    permissions:
      contents: write
      issues: write

    steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-python@v5
      with:
        python-version: '3.12'

    - name: Install dependencies
      run: pip install -e ".[dev]"

    - name: Fetch Copilot models
      env:
        COPILOT_TOKEN: ${{ secrets.COPILOT_TOKEN }}
        GH_PAT: ${{ secrets.GH_PAT }}
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        GITHUB_REPOSITORY: ${{ github.repository }}
        GITHUB_ACTOR: ${{ github.actor }}
        GITHUB_EVENT_NAME: ${{ github.event_name }}
      run: python -m copilot_fetcher fetch

    - name: Commit to release branch
      run: |
        # Commits models/ directory (only) to release branch
        # Creates dated snapshots and git tags
```

### Release Branch

The `release` branch contains **only** the `models/` directory:
- `models/copilot-models.json` — Latest model list
- `models/copilot-models-YYYY-MM-DD.json` — Dated snapshot

Each successful run also creates a git tag: `vYYYY-MM-DD-HHMMSS`

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `COPILOT_TOKEN` | Yes | OAuth token (`gho_*`) for Copilot API calls. Space-only values are trimmed |
| `GH_PAT` | For caching | PAT with `repo` scope, used only for `gh secret set` authentication |
| `GITHUB_TOKEN` | In Actions | Auto-provided by GitHub Actions |
| `GITHUB_REPOSITORY` | In Actions | Auto-provided by GitHub Actions |
| `GITHUB_ACTOR` | In Actions | Auto-provided by GitHub Actions |
| `GITHUB_EVENT_NAME` | In Actions | Auto-provided by GitHub Actions |

## Troubleshooting

### "GitHub CLI is not authenticated"

```bash
gh auth login
```

### "gh command not found"

Install GitHub CLI: https://cli.github.com/

### "No models found"

Run fetch command:

```bash
./run.sh fetch
```

### GitHub Actions "Personal Access Tokens are not supported"

**This is expected if COPILOT_TOKEN is a PAT or empty.** The Copilot API only accepts OAuth tokens.

**Solutions:**

1. **Use device flow** (for Actions):
   - Ensure `GH_PAT` and `COPILOT_TOKEN` secrets are configured
   - Trigger workflow manually (`workflow_dispatch`)
   - Follow the link + code in the Actions logs
   - The new token will be cached to `COPILOT_TOKEN` automatically

2. **Use local scheduling**:
   ```bash
   # Add to crontab
   0 0 * * * cd /path/to/repo && ./run.sh fetch
   ```

3. **Run manually when needed**:
   ```bash
   gh auth login  # Interactive authentication
   ./run.sh fetch
   ```

### Scheduled Run Created an Issue

When a scheduled run fails due to an expired/missing token, the workflow automatically creates a GitHub Issue and @mentions you. To fix it:

1. Go to the Issue and click the link to Actions
2. Trigger the workflow manually (`workflow_dispatch`)
3. Complete the device flow in the logs
4. The new token will be cached automatically

### Token Expired

OAuth tokens from device flow typically expire after 8 hours. When this happens:
- **Manual trigger**: Device flow will re-authenticate automatically
- **Scheduled trigger**: Workflow fails and creates an Issue to notify you

### "Could not cache token"

If device flow succeeds but shows "Could not cache token", check that:
- `GH_PAT` secret is set to a valid PAT with `repo` scope
- The PAT has not expired

## Project Structure

```
.
├── src/
│   └── copilot_fetcher/
│       ├── __init__.py        # Package entry
│       ├── __main__.py        # CLI entry point
│       ├── gh_auth.py         # GitHub CLI authentication
│       ├── api.py             # API client (httpx + gh CLI fallback)
│       ├── storage.py         # Local data storage
│       ├── device_flow.py     # OAuth device flow (RFC 8628)
│       ├── tui.py             # Interactive terminal UI
│       └── copilot_cli.py     # Copilot CLI utilities
├── .github/
│   └── workflows/
│       └── daily-fetch.yml    # GitHub Actions workflow
├── run.sh                     # Launch script
├── set_env.sh                 # Environment setup
├── pyproject.toml             # Project config
├── uv.lock                    # Lock file
└── README.md                  # This document
```

## License

MIT
