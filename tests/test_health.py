"""Tests for health check tool."""

import pytest
from agentic_msteams_mcp.tools.health import msteams_health_check

def test_health_check():
    """Test the health check function."""
    result = msteams_health_check()
    
    assert isinstance(result, dict)
    assert "status" in result
    assert "service" in result
    assert "checks" in result
    
    assert result["status"] == "ok"
    assert result["service"] == "msteams-mcp"
