# Tasks: LiteLLM Config Generation

## Task 1: Create Config Generator Module
- [x] Create `src/copilot_fetcher/litellm_config.py`
- [x] Implement `LiteLLMConfigGenerator` class
- [x] Implement provider mapping (`github/{id}`)
- [x] Implement YAML output
- [x] Implement JSON output
- [x] Add unit tests

## Task 2: Add CLI Command
- [x] Add `litellm-config` subparser to `__main__.py`
- [x] Implement command handler
- [x] Support `--format`, `--output`, `--api-key-env` options
- [x] Add integration tests

## Task 3: Update Dependencies
- [x] Add `pyyaml` to `pyproject.toml` dependencies
- [x] Lock dependencies with `uv lock`

## Task 4: Update Workflow
- [x] Modify `.github/workflows/daily-fetch.yml`
- [x] Add config generation step after fetch
- [x] Update commit step to include config files
- [x] Update workflow summary to mention config files

## Task 5: Documentation
- [x] Update README.md with `litellm-config` command
- [x] Add LiteLLM usage example
- [x] Document config file format

## Task 6: Testing & Validation
- [x] Run unit tests
- [x] Run ruff linting
- [x] Verify workflow YAML syntax
- [x] Test config generation locally
