"""Main module for agentic-msteams-mcp."""

from fastapi import FastAPI


# ── Teams HTTP surface only (bot /messages endpoint) ───────────────────────
# v0.1.0: This app is purely a Teams webhook surface.
# The MCP server runs independently via stdio (see mcp_server.py).
# There are NO fake /tools or /mcp routes on this HTTP server.


__version__: str = "0.1.0"

app = FastAPI(
    title="Agentic Microsoft Teams MCP Server",
    version=__version__,
    description="Teams bot HTTP surface (not an MCP server surface)",
)


@app.get("/api/messages")
async def _messages() -> dict:  # noqa: A001
    """Placeholder webhook endpoint for Teams bot integration."""
    return {"message": "Webhook endpoint"}


@app.get("/")
async def _root() -> dict:  # noqa: A001
    return {"message": "Agentic Microsoft Teams MCP Server"}
