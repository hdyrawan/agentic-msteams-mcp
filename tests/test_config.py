"""Tests for configuration module."""

import pytest
from agentic_msteams_mcp.config import settings, Settings

def test_settings_loaded():
    """Test that settings can be loaded."""
    # This is just a placeholder test - actual tests would be more comprehensive
    assert hasattr(settings, 'teams_app_id')
    assert hasattr(settings, 'teams_app_password')

def test_default_values():
    """Test default configuration values."""
    assert settings.server_host == "localhost"
    assert settings.server_port == 8000
    assert settings.mcp_server_host == "localhost"
    assert settings.mcp_server_port == 8001