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
