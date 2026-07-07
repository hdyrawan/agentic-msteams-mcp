"""Initialization for agentic_msteams_mcp tools."""

# Import all tools here to make them available as a module
from .health import msteams_health_check

__all__ = [
    "msteams_health_check"
]
