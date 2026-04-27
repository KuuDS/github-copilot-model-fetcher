"""Tests for CLI litellm-config command."""

from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest

from copilot_fetcher.__main__ import generate_litellm_config_command


class TestGenerateLitellmConfigCommand:
    """Test generate_litellm_config_command function."""

    def test_stdout_output(self, capsys):
        """Test output to stdout when no output path given."""
        storage = MagicMock()
        storage.get_raw_models.return_value = {
            "data": [
                {"id": "gpt-4o", "name": "GPT-4o"},
            ]
        }

        generate_litellm_config_command(storage, format="yaml")

        captured = capsys.readouterr()
        assert "model_list:" in captured.out
        assert "gpt-4o" in captured.out

    def test_json_stdout(self, capsys):
        """Test JSON output to stdout."""
        storage = MagicMock()
        storage.get_raw_models.return_value = {
            "data": [
                {"id": "gpt-4o", "name": "GPT-4o"},
            ]
        }

        generate_litellm_config_command(storage, format="json")

        captured = capsys.readouterr()
        parsed = json.loads(captured.out)
        assert "model_list" in parsed

    def test_file_output(self, tmp_path):
        """Test output to file."""
        storage = MagicMock()
        storage.get_raw_models.return_value = {
            "data": [
                {"id": "gpt-4o", "name": "GPT-4o"},
            ]
        }

        output = tmp_path / "config.yaml"
        generate_litellm_config_command(storage, format="yaml", output=output)

        assert output.exists()
        content = output.read_text()
        assert "model_list:" in content

    def test_no_models_error(self):
        """Test error when no models stored."""
        storage = MagicMock()
        storage.get_raw_models.return_value = None

        with pytest.raises(SystemExit) as exc_info:
            generate_litellm_config_command(storage)
        assert exc_info.value.code == 1

    def test_empty_models_error(self):
        """Test error when models list is empty."""
        storage = MagicMock()
        storage.get_raw_models.return_value = {"data": []}

        with pytest.raises(SystemExit) as exc_info:
            generate_litellm_config_command(storage)
        assert exc_info.value.code == 1

    def test_custom_api_key_env(self, capsys):
        """Test custom API key environment variable."""
        storage = MagicMock()
        storage.get_raw_models.return_value = {
            "data": [
                {"id": "gpt-4o", "name": "GPT-4o"},
            ]
        }

        generate_litellm_config_command(storage, format="yaml", api_key_env="CUSTOM_TOKEN")

        captured = capsys.readouterr()
        assert "os.environ/CUSTOM_TOKEN" in captured.out

    def test_api_base(self, capsys):
        """Test custom API base URL."""
        storage = MagicMock()
        storage.get_raw_models.return_value = {
            "data": [
                {"id": "gpt-4o", "name": "GPT-4o"},
            ]
        }

        generate_litellm_config_command(
            storage, format="yaml", api_base="https://custom.example.com"
        )

        captured = capsys.readouterr()
        assert "https://custom.example.com" in captured.out
