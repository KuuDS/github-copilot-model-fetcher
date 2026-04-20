# GitHub Copilot Model Fetcher

Fetch available GitHub Copilot models using GitHub CLI authentication.

Gets the complete **35+ model list** including Claude, GPT-5, Gemini, Grok, and more.

## Features

- GitHub CLI authentication
- Fetch complete Copilot model list (35+ models)
- Group models by provider
- Local JSON storage
- Command-line tool

## Installation

```bash
# Clone repository
git clone https://github.com/KuuDS/github-copilot-model-fetcher.git
cd github-copilot-model-fetcher

# Install dependencies
uv pip install -e .
# or: pip install -e .
```

## Prerequisites

Install and configure **GitHub CLI**:

```bash
# Install GitHub CLI
# https://cli.github.com/

# Login
gh auth login
```

## Usage

### Check authentication status

```bash
./run.sh status
```

### Fetch model list

```bash
./run.sh fetch
```

Output:
```
✓ Using GitHub CLI (gh) authentication
  Accessing full Copilot model list (35+ models)

Fetching Copilot models...
✓ Fetched 35 models
✓ Saved to: ~/.copilot-fetcher/models.json
```

### List models

```bash
./run.sh list
```

Example output:

```
================================================================================
GitHub Copilot Models (fetched: 2026-03-23T16:28:24)
================================================================================

【Anthropic Claude】
  • claude-opus-4.6
    (Claude Opus 4.6)
  • claude-sonnet-4.6
    (Claude Sonnet 4.6)
  • claude-haiku-4.5
    (Claude Haiku 4.5)
  • ...

【OpenAI GPT】
  • gpt-5.4
    (GPT-5.4)
  • gpt-4.1
    (GPT-4.1)
  • gpt-5.1-codex
    (GPT-5.1-Codex)
  • ...

【Google Gemini】
  • gemini-2.5-pro
    (Gemini 2.5 Pro)

【xAI Grok】
  • grok-code-fast-1
    (Grok Code Fast 1)

================================================================================
Total: 35 models
================================================================================
```

### View raw JSON

```bash
./run.sh raw
```

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

- `token.json` - Access token (permissions 600)
- `models.json` - Fetched model list

## API Reference

### Python API

```python
from copilot_fetcher import CopilotClient, get_gh_token

# Get GitHub CLI token
token = get_gh_token()

# Use client
with CopilotClient(token) as client:
    response = client.get_models()
    for model in response.models:
        print(f"{model.name}: {model.id}")
```

### Modules

- `copilot_fetcher.gh_auth` - GitHub CLI authentication
- `copilot_fetcher.api` - GitHub Copilot API client
- `copilot_fetcher.storage` - Local data storage

## GitHub Actions Device Flow Setup

This project supports **interactive OAuth device flow** in GitHub Actions. When you manually trigger the workflow, it displays a verification link and code in the Actions logs. You scan/authorize, and the OAuth token is automatically cached for future runs.

### Setup Steps

1. **Create an OAuth App**:
   - Go to GitHub Settings → Developer settings → OAuth Apps → New OAuth App
   - Application name: `Copilot Model Fetcher`
   - Homepage URL: `https://github.com/{your-username}/github-copilot-model-info-fetcher`
   - Authorization callback URL: `http://localhost`
   - Save and copy the **Client ID** (you do NOT need the Client Secret)

2. **Add Repository Secret**:
   - Go to Repository Settings → Secrets and variables → Actions → New repository secret
   - Name: `OAUTH_CLIENT_ID`
   - Value: The Client ID from step 1

3. **Trigger Workflow Manually**:
   - Go to Actions → "Daily Copilot Models Fetch" → "Run workflow"
   - Open the workflow run logs
   - You will see a link and a user code - open the link and enter the code
   - After authorization, the OAuth token is automatically cached in `GH_TOKEN` secret

### Trigger Behavior

| Trigger Type | Device Flow | On Token Failure |
|-------------|-------------|------------------|
| `workflow_dispatch` (manual) | Enabled - shows link + code | Creates issue to notify you |
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
    # Uses default permissions (repo scope) for secret updates and issue creation

    steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-python@v5
      with:
        python-version: '3.12'

    - name: Install dependencies
      run: pip install -e ".[dev]"

    - name: Fetch Copilot models
      env:
        GH_TOKEN: ${{ secrets.GH_TOKEN }}
        OAUTH_CLIENT_ID: ${{ secrets.OAUTH_CLIENT_ID }}
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        GITHUB_REPOSITORY: ${{ github.repository }}
        GITHUB_ACTOR: ${{ github.actor }}
        GITHUB_EVENT_NAME: ${{ github.event_name }}
      run: python -m copilot_fetcher fetch

    - name: Commit to release branch
      run: |
        # Commits models to release branch
        # Creates dated snapshots

    - name: Create Release
      run: |
        # Creates GitHub Release with model files
```

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GH_TOKEN` | Yes* | OAuth token (`gho_*`) or PAT (`ghp_*`). OAuth works; PAT triggers device flow |
| `OAUTH_CLIENT_ID` | For device flow | Your OAuth App's Client ID |
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

Or use environment variable authentication:

```bash
export GH_TOKEN="your_github_token"
python -m copilot_fetcher fetch
```

### "No models found"

Run fetch command:

```bash
./run.sh fetch
```

### GitHub Actions "Personal Access Tokens are not supported"

**This is expected if you are using a PAT.** The Copilot API only accepts OAuth tokens.

**Solutions:**

1. **Use device flow** (for Actions):
   - Set `OAUTH_CLIENT_ID` secret
   - Trigger workflow manually (`workflow_dispatch`)
   - Follow the link + code in the Actions logs

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

OAuth tokens from `gh auth login` typically expire after 8 hours. When this happens:
- **Manual trigger**: Device flow will re-authenticate automatically
- **Scheduled trigger**: Workflow fails and creates an Issue to notify you

### "Device flow not configured"

You need to create an OAuth App and add `OAUTH_CLIENT_ID` as a repository secret. See [GitHub Actions Device Flow Setup](#github-actions-device-flow-setup) above.

## Project Structure

```
.
├── src/
│   └── copilot_fetcher/
│       ├── __init__.py      # Package entry
│       ├── __main__.py      # CLI entry
│       ├── gh_auth.py       # GitHub CLI auth
│       ├── api.py           # API client
│       └── storage.py       # Data storage
├── run.sh                   # Launch script
├── pyproject.toml           # Project config
└── README.md               # This document
```

## License

MIT
