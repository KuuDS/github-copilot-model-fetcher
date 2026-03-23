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

## GitHub Actions Automation

You can automatically fetch Copilot models daily using GitHub Actions.

### ⚠️ Important Note

**Personal Access Tokens (PAT) are NOT supported** by the GitHub Copilot API `/models` endpoint. 
The workflow uses GitHub CLI (`gh`) with token authentication instead.

### Setup

1. **Create a Personal Access Token**:
   - Go to https://github.com/settings/tokens
   - Click "Generate new token (classic)"
   - Select scopes: `repo`, `read:user`
   - Copy the generated token

2. **Add Token to Repository Secrets**:
   - Go to your repository on GitHub
   - Navigate to Settings → Secrets and variables → Actions
   - Click "New repository secret"
   - Name: `GH_TOKEN`
   - Value: Your personal access token from step 1
   - Click "Add secret"

3. **Enable GitHub Actions**:
   - The workflow file `.github/workflows/daily-fetch.yml` is already included
   - Actions will run automatically at 00:00 UTC every day
   - You can also trigger manually from Actions tab

### What the Workflow Does

- **Schedule**: Runs daily at 00:00 UTC (configurable in the workflow)
- **Manual Trigger**: Can be triggered manually from GitHub Actions tab
- **Output**:
  - Commits models to the `release` branch
  - Creates/updates a GitHub Release with model snapshots
  - Archives dated snapshots for historical tracking

### Workflow Configuration

The workflow is defined in `.github/workflows/daily-fetch.yml`:

```yaml
name: Daily Copilot Models Fetch

on:
  schedule:
    - cron: '0 0 * * *'  # Daily at 00:00 UTC
  workflow_dispatch:     # Allow manual trigger

jobs:
  fetch-models:
    runs-on: ubuntu-latest
    permissions:
      contents: write
    
    steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-python@v5
      with:
        python-version: '3.12'
    
    - name: Install dependencies
      run: pip install -e .
    
    - name: Install GitHub CLI
      uses: dev-hanz-ala/install-gh-cli-action@latest
      with:
        gh-cli-version: 2.67.0
    
    - name: Authenticate GitHub CLI
      env:
        GH_TOKEN: ${{ secrets.GH_TOKEN }}
      run: |
        echo "$GH_TOKEN" | gh auth login --with-token
        gh auth status
    
    - name: Fetch Copilot models
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

The tool supports two authentication methods:

| Method | Environment Variable | Use Case |
|--------|---------------------|----------|
| GitHub CLI Token | `gh auth token` | Local development |
| Personal Access Token | `GH_TOKEN` | GitHub Actions, CI/CD |

For GitHub Actions, set `GH_TOKEN` in your repository secrets.

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

The GitHub Copilot API `/models` endpoint **does not accept Personal Access Tokens (PAT)** directly.

The workflow already handles this by:
1. Installing GitHub CLI in the runner
2. Authenticating `gh` with your PAT: `echo "$GH_TOKEN" | gh auth login --with-token`
3. Using `gh auth token` to get a compatible token

If you're seeing this error, ensure:
- The `GH_TOKEN` secret is set correctly
- The workflow includes the GitHub CLI installation step

### GitHub Actions "Resource not accessible"

Ensure the workflow has proper permissions:

```yaml
permissions:
  contents: write
```

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
