# Tasks: LiteLLM Config Generation

## Task 1: Create Config Generator Module
- [ ] Create `src/copilot_fetcher/litellm_config.py`
- [ ] Implement `LiteLLMConfigGenerator` class
- [ ] Implement provider mapping (`github/{id}`)
- [ ] Implement YAML output
- [ ] Implement JSON output
- [ ] Add unit tests

## Task 2: Add CLI Command
- [ ] Add `litellm-config` subparser to `__main__.py`
- [ ] Implement command handler
- [ ] Support `--format`, `--output`, `--api-key-env` options
- [ ] Add integration tests

## Task 3: Update Dependencies
- [ ] Add `pyyaml` to `pyproject.toml` dependencies
- [ ] Lock dependencies with `uv lock`

## Task 4: Update Workflow
- [ ] Modify `.github/workflows/daily-fetch.yml`
- [ ] Add config generation step after fetch
- [ ] Update commit step to include config files
- [ ] Update workflow summary to mention config files

## Task 5: Documentation
- [ ] Update README.md with `litellm-config` command
- [ ] Add LiteLLM usage example
- [ ] Document config file format

## Task 6: Testing & Validation
- [ ] Run unit tests
- [ ] Run ruff linting
- [ ] Verify workflow YAML syntax
- [ ] Test config generation locally
