"""Tests for configuration module."""

import pytest
from agentic_msteams_mcp.config import settings, Settings

def test_settings_loaded():
    """Test that settings can be loaded."""
    assert hasattr(settings, 'teams_app_id')
    assert hasattr(settings, 'teams_app_password')

def test_default_values():
    """Test default configuration values."""
    assert settings.server_host == "127.0.0.1"
    assert settings.server_port == 8000
    assert settings.mcp_server_host == "127.0.0.1"
    assert settings.mcp_server_port == 8001
    # Durable state defaults (v0.5.0a)
    assert settings.msteams_use_durable_state is False
    assert settings.msteams_state_store_path == "data/state.json"

def test_durable_config_env_overrides(monkeypatch):
    """Test that environment variables override durable state config."""
    monkeypatch.setenv("MSTEAMS_USE_DURABLE_STATE", "True")
    monkeypatch.setenv("MSTEAMS_STATE_STORE_PATH", "tmp/custom-state.json")
    
    # Create a new Settings instance to ensure fresh load from env
    s = Settings()
    assert s.msteams_use_durable_state is True
    assert s.msteams_state_store_path == "tmp/custom-state.json"
