"""LiteLLM configuration generator from Copilot models."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml


class LiteLLMConfigGenerator:
    """Generates LiteLLM configuration from Copilot models."""

    def __init__(
        self,
        api_key_env: str = "GITHUB_TOKEN",
        api_base: str | None = None,
        include_model_info: bool = True,
    ) -> None:
        """Initialize the config generator.

        Args:
            api_key_env: Environment variable name for the API key
            api_base: Optional custom API base URL
            include_model_info: Whether to include model_info in output
        """
        self.api_key_env = api_key_env
        self.api_base = api_base
        self.include_model_info = include_model_info

    def generate(self, models: list[dict[str, Any]]) -> dict[str, Any]:
        """Generate LiteLLM config dict from Copilot models.

        Args:
            models: List of model dicts from the Copilot API

        Returns:
            LiteLLM configuration dict with model_list
        """
        model_list = []
        for model_data in models:
            model_id = model_data.get("id", "")
            if not model_id:
                continue

            entry: dict[str, Any] = {
                "model_name": model_id,
                "litellm_params": {
                    "model": f"github/{model_id}",
                    "api_key": f"os.environ/{self.api_key_env}",
                },
            }

            if self.api_base:
                entry["litellm_params"]["api_base"] = self.api_base

            if self.include_model_info:
                model_info: dict[str, Any] = {
                    "id": model_id,
                }

                if "name" in model_data:
                    model_info["name"] = model_data["name"]
                if "description" in model_data:
                    model_info["description"] = model_data["description"]
                if "capabilities" in model_data:
                    model_info["capabilities"] = model_data["capabilities"]
                if "limits" in model_data:
                    model_info["limits"] = model_data["limits"]
                if "provider" in model_data:
                    model_info["provider"] = model_data["provider"]
                if "version" in model_data:
                    model_info["version"] = model_data["version"]

                entry["model_info"] = model_info

            model_list.append(entry)

        return {"model_list": model_list}

    def to_yaml(self, config: dict[str, Any]) -> str:
        """Convert config dict to YAML string.

        Args:
            config: LiteLLM configuration dict

        Returns:
            YAML formatted string
        """
        return yaml.dump(
            config,
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True,
            width=120,
        )

    def to_json(self, config: dict[str, Any]) -> str:
        """Convert config dict to JSON string.

        Args:
            config: LiteLLM configuration dict

        Returns:
            JSON formatted string
        """
        return json.dumps(config, indent=2, ensure_ascii=False)

    def generate_from_raw(self, raw_data: dict[str, Any]) -> dict[str, Any]:
        """Generate config from raw API response.

        Args:
            raw_data: Raw API response dict

        Returns:
            LiteLLM configuration dict
        """
        models = raw_data.get("data", [])
        return self.generate(models)


def generate_litellm_config(
    models: list[dict[str, Any]],
    format: str = "yaml",
    api_key_env: str = "GITHUB_TOKEN",
    api_base: str | None = None,
) -> str:
    """Generate LiteLLM config string from models.

    Args:
        models: List of model dicts
        format: Output format ("yaml" or "json")
        api_key_env: Environment variable for API key
        api_base: Optional API base URL

    Returns:
        Config string in the requested format
    """
    generator = LiteLLMConfigGenerator(
        api_key_env=api_key_env,
        api_base=api_base,
    )
    config = generator.generate(models)

    if format == "yaml":
        return generator.to_yaml(config)
    elif format == "json":
        return generator.to_json(config)
    else:
        raise ValueError(f"Unsupported format: {format}")


def write_config(
    config_str: str,
    output_path: Path | str,
) -> Path:
    """Write config string to file.

    Args:
        config_str: Config string to write
        output_path: Output file path

    Returns:
        Resolved output path
    """
    output = Path(output_path)

    # If output is a directory, use default filename
    if output.is_dir():
        output = output / "litellm-config.yaml"

    # Create parent directories if needed
    output.parent.mkdir(parents=True, exist_ok=True)

    with open(output, "w") as f:
        f.write(config_str)

    return output
