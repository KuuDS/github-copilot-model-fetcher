# Design: LiteLLM Config Generation

## Module Design

### `copilot_fetcher/litellm_config.py`

```python
class LiteLLMConfigGenerator:
    """Generates LiteLLM configuration from Copilot models."""

    def __init__(
        self,
        api_key_env: str = "GITHUB_TOKEN",
        api_base: str | None = None,
        include_model_info: bool = True,
    ) -> None:
        ...

    def generate(self, models: list[dict[str, Any]]) -> dict[str, Any]:
        """Generate LiteLLM config dict."""
        ...

    def to_yaml(self, config: dict[str, Any]) -> str:
        ...

    def to_json(self, config: dict[str, Any]) -> str:
        ...
```

### Provider Mapping

Copilot model IDs map directly to LiteLLM `github` provider:

| Copilot ID | LiteLLM Model |
|------------|---------------|
| `gpt-4o` | `github/gpt-4o` |
| `claude-sonnet-4` | `github/claude-sonnet-4` |
| `gemini-2.5-pro` | `github/gemini-2.5-pro` |

The mapping rule is: `github/{copilot_model_id}`

### Config Structure

```yaml
model_list:
  - model_name: {copilot_id}
    litellm_params:
      model: github/{copilot_id}
      api_key: os.environ/{api_key_env}
      api_base: {api_base}  # optional
    model_info:
      id: {copilot_id}
      name: {name}
      description: {description}
      capabilities: {capabilities}
      limits: {limits}
      provider: {provider}
```

### CLI Integration

```python
# In __main__.py
litellm_parser = subparsers.add_parser("litellm-config", help="Generate LiteLLM config")
litellm_parser.add_argument("--format", choices=["yaml", "json"], default="yaml")
litellm_parser.add_argument("--output", type=Path, default=None)
litellm_parser.add_argument("--api-key-env", default="GITHUB_TOKEN")
```

### Workflow Integration

The `daily-fetch.yml` workflow will:

1. Fetch models (existing)
2. Generate configs:
   ```bash
   python -m copilot_fetcher litellm-config \
     --output /tmp/models-export/litellm-config.yaml
   python -m copilot_fetcher litellm-config --format json \
     --output /tmp/models-export/litellm-config.json
   ```
3. Copy to release branch (existing pattern)

## Dependencies

- Add `pyyaml` to project dependencies for YAML generation
- `json` is in stdlib

## Error Handling

- If no models fetched, exit with error message
- If output path is directory, use default filename
- If output path parent doesn't exist, create it

## Testing Strategy

1. Unit tests with mock model data
2. Verify YAML/JSON output structure matches LiteLLM schema
3. CLI integration tests using subprocess
