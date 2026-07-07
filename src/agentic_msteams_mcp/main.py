"""Main entry point for agentic-msteams-mcp."""

import asyncio
import sys

import uvicorn

from . import app
from .mcp_server import mcp_server


def main():  # noqa: A01
    """Start both the Teams HTTP surface and the MCP stdio server."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # Start MCP stdio in background
    mcp_task = loop.create_task(mcp_server.run_stdio_async())

    # Run uvicorn for Teams (main thread blocks here)
    try:
        uvicorn.run(
            app,
            host="127.0.0.1",  # localhost bind by default
            port=8000,
            log_level="info",
        )
    except KeyboardInterrupt:  # noqa: E722
        mcp_task.cancel()
        loop.run_until_complete(mcp_task)


if __name__ == "__main__":
    main()
