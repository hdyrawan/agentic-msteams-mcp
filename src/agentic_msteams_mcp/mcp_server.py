"""Real MCP protocol server for agentic-msteams-mcp (stdio transport).

This module uses the official MCP Python SDK's FastMCP so clients can call
tools via ``tools/list``, ``tools/call`` etc. over stdio — NOT via HTTP GET/
POST endpoints masquerading as MCP.

v0.1.0 closed-world inventory: only ``msteams_health_check``.
"""

from typing import Any, Dict

# Import the real business logic from tools/health.py for re-export
from .tools.health import msteams_health_check as _real_health_check  # noqa: F401


# ── MCP server instance (stdio transport by default) ──────────────────────

from mcp.server.fastmcp import FastMCP as _FastMCP


def _register_tools(mcp: _FastMCP) -> None:
    """Register v0.1.0 tools on the given MCP server."""

    @mcp.tool(
        name="msteams_health_check",
        description="Check Microsoft Teams server health"
    )
    async def _impl() -> Dict[str, Any]:  # noqa: A001
        """Proxy that calls the real business logic."""
        return _real_health_check(**{})


# Create the MCP server (stdio transport by default, localhost bind)
mcp_server = _FastMCP(
    name="agentic-msteams-mcp",
    host="127.0.0.1",
    port=8000,
)

# Register tools after server creation
_register_tools(mcp_server)
