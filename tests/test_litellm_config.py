"""Tests for LiteLLM config generator."""

from __future__ import annotations

import json

import pytest
import yaml

from copilot_fetcher.litellm_config import (
    LiteLLMConfigGenerator,
    generate_litellm_config,
    write_config,
)


@pytest.fixture
def sample_models():
    """Sample model data for testing."""
    return [
        {
            "id": "gpt-4o",
            "name": "GPT-4o",
            "version": "2024-05-13",
            "description": "OpenAI GPT-4o model",
            "capabilities": {"vision": True, "tools": True},
            "limits": {"max_tokens": 4096},
            "provider": "openai",
        },
        {
            "id": "claude-sonnet-4",
            "name": "Claude Sonnet 4",
            "version": "2024-01-01",
            "description": "Anthropic Claude Sonnet 4",
            "capabilities": {"vision": True},
            "limits": {"max_tokens": 8192},
            "provider": "anthropic",
        },
    ]


class TestLiteLLMConfigGenerator:
    """Test LiteLLMConfigGenerator class."""

    def test_generate_basic(self, sample_models):
        """Test basic config generation."""
        generator = LiteLLMConfigGenerator()
        config = generator.generate(sample_models)

        assert "model_list" in config
        assert len(config["model_list"]) == 2

        first = config["model_list"][0]
        assert first["model_name"] == "gpt-4o"
        assert first["litellm_params"]["model"] == "github/gpt-4o"
        assert first["litellm_params"]["api_key"] == "os.environ/GITHUB_TOKEN"

    def test_generate_with_api_key_env(self, sample_models):
        """Test custom API key environment variable."""
        generator = LiteLLMConfigGenerator(api_key_env="MY_TOKEN")
        config = generator.generate(sample_models)

        assert config["model_list"][0]["litellm_params"]["api_key"] == "os.environ/MY_TOKEN"

    def test_generate_with_api_base(self, sample_models):
        """Test custom API base URL."""
        generator = LiteLLMConfigGenerator(api_base="https://custom.example.com")
        config = generator.generate(sample_models)

        assert config["model_list"][0]["litellm_params"]["api_base"] == "https://custom.example.com"

    def test_generate_without_model_info(self, sample_models):
        """Test generation without model_info."""
        generator = LiteLLMConfigGenerator(include_model_info=False)
        config = generator.generate(sample_models)

        assert "model_info" not in config["model_list"][0]

    def test_generate_model_info_content(self, sample_models):
        """Test model_info contains expected fields."""
        generator = LiteLLMConfigGenerator()
        config = generator.generate(sample_models)

        model_info = config["model_list"][0]["model_info"]
        assert model_info["id"] == "gpt-4o"
        assert model_info["name"] == "GPT-4o"
        assert model_info["description"] == "OpenAI GPT-4o model"
        assert model_info["capabilities"]["vision"] is True
        assert model_info["limits"]["max_tokens"] == 4096
        assert model_info["provider"] == "openai"
        assert model_info["version"] == "2024-05-13"

    def test_generate_skips_empty_id(self):
        """Test that models without id are skipped."""
        models = [{"name": "No ID"}, {"id": "valid", "name": "Valid"}]
        generator = LiteLLMConfigGenerator()
        config = generator.generate(models)

        assert len(config["model_list"]) == 1
        assert config["model_list"][0]["model_name"] == "valid"

    def test_to_yaml(self, sample_models):
        """Test YAML output."""
        generator = LiteLLMConfigGenerator()
        config = generator.generate(sample_models)
        yaml_str = generator.to_yaml(config)

        parsed = yaml.safe_load(yaml_str)
        assert "model_list" in parsed
        assert len(parsed["model_list"]) == 2

    def test_to_json(self, sample_models):
        """Test JSON output."""
        generator = LiteLLMConfigGenerator()
        config = generator.generate(sample_models)
        json_str = generator.to_json(config)

        parsed = json.loads(json_str)
        assert "model_list" in parsed
        assert len(parsed["model_list"]) == 2

    def test_generate_from_raw(self, sample_models):
        """Test generation from raw API response."""
        raw_data = {"data": sample_models, "total": 2}
        generator = LiteLLMConfigGenerator()
        config = generator.generate_from_raw(raw_data)

        assert len(config["model_list"]) == 2


class TestGenerateLiteLLMConfig:
    """Test generate_litellm_config function."""

    def test_generate_yaml(self, sample_models):
        """Test YAML generation."""
        result = generate_litellm_config(sample_models, format="yaml")
        parsed = yaml.safe_load(result)
        assert "model_list" in parsed

    def test_generate_json(self, sample_models):
        """Test JSON generation."""
        result = generate_litellm_config(sample_models, format="json")
        parsed = json.loads(result)
        assert "model_list" in parsed

    def test_invalid_format(self, sample_models):
        """Test invalid format raises error."""
        with pytest.raises(ValueError, match="Unsupported format: xml"):
            generate_litellm_config(sample_models, format="xml")


class TestWriteConfig:
    """Test write_config function."""

    def test_write_to_file(self, tmp_path):
        """Test writing config to file."""
        output = tmp_path / "config.yaml"
        result = write_config("test config", output)

        assert result == output
        assert output.read_text() == "test config"

    def test_write_to_directory(self, tmp_path):
        """Test writing to directory uses default filename."""
        result = write_config("test config", tmp_path)

        assert result == tmp_path / "litellm-config.yaml"
        assert result.read_text() == "test config"

    def test_create_parent_dirs(self, tmp_path):
        """Test parent directories are created."""
        output = tmp_path / "nested" / "deep" / "config.yaml"
        result = write_config("test config", output)

        assert result == output
        assert output.read_text() == "test config"
