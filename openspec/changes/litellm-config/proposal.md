# LiteLLM Config Generation

## Problem

Users of this tool want to consume the fetched GitHub Copilot models through [LiteLLM](https://github.com/BerriAI/litellm) - a unified interface for 100+ LLMs. Currently, the tool only releases the raw `models.json` on the `release` branch. Users must manually map Copilot model IDs to LiteLLM configuration format.

## Goal

Automatically generate and release a LiteLLM-compatible configuration file alongside the raw model data in the `daily-fetch` workflow.

## Solution Overview

Add a config generator module and CLI command that transforms the fetched Copilot models into LiteLLM's `model_list` format. Run this automatically in CI and commit the output to the `release` branch.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Daily Fetch Workflow                      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  python -m copilot_fetcher fetch                            │
│  → ~/.copilot-fetcher/models.json (raw API response)        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  python -m copilot_fetcher litellm-config                   │
│  → ~/.copilot-fetcher/litellm-config.yaml                   │
│  → ~/.copilot-fetcher/litellm-config.json                   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  Commit to release branch                                   │
│  models/copilot-models.json                                 │
│  models/litellm-config.yaml                                 │
│  models/litellm-config.json                                 │
└─────────────────────────────────────────────────────────────┘
```

## LiteLLM Config Format

LiteLLM uses a `model_list` array in YAML:

```yaml
model_list:
  - model_name: gpt-4o
    litellm_params:
      model: github/gpt-4o
      api_key: os.environ/GITHUB_TOKEN
      api_base: https://models.inference.ai.azure.com
    model_info:
      id: gpt-4o
      description: OpenAI GPT-4o model
      capabilities:
        vision: true
        tools: true
```

GitHub Copilot models map to the `github` provider in LiteLLM (which proxies to GitHub Models / Azure AI Inference). The model ID from Copilot API becomes `github/<id>`.

## Changes Required

### 1. New Module: `copilot_fetcher/litellm_config.py`

- Load models from `Storage`
- Generate `model_list` entries for each model
- Output YAML and JSON formats
- Support configurable `api_key` environment variable name
- Include model metadata (capabilities, limits) in `model_info`

### 2. CLI Update: `copilot_fetcher/__main__.py`

New subcommand:
```bash
python -m copilot_fetcher litellm-config [--format yaml|json] [--output PATH] [--api-key-env VAR]
```

### 3. Workflow Update: `.github/workflows/daily-fetch.yml`

After `fetch` step, add:
```bash
python -m copilot_fetcher litellm-config --output ~/.copilot-fetcher/litellm-config.yaml
python -m copilot_fetcher litellm-config --format json --output ~/.copilot-fetcher/litellm-config.json
```

Then copy both to `/tmp/models-export/` and commit to `release` branch.

### 4. Tests

- Unit tests for config generation
- Integration test for CLI command
- Verify YAML/JSON output structure

## Non-goals

- Custom provider implementation (we use LiteLLM's built-in `github` provider)
- Runtime LiteLLM proxy (we only generate config files)
- Model capability validation (we trust the Copilot API response)

## Open Questions

1. Should we include `api_base` in the config? GitHub Models uses Azure AI Inference endpoint (`models.inference.ai.azure.com`), but Copilot models might be accessible through a different endpoint via LiteLLM.
2. Should we filter out non-chat models (embeddings) from the LiteLLM config?
3. Should the config support multiple API key sources (env var, direct string)?

## Success Criteria

- [ ] `litellm-config` command generates valid YAML
- [ ] `litellm-config --format json` generates valid JSON
- [ ] Daily workflow commits config files to release branch
- [ ] Config file can be used directly with LiteLLM proxy
