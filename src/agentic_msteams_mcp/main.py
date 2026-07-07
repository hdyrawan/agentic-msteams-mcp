"""Main entry point for agentic-msteams-mcp."""

import asyncio
import sys
import argparse
import uvicorn

from .mcp_server import mcp_server
from .teams_app import teams_app
from .config import settings

def run_mcp_stdio():
    """Run the MCP stdio server."""
    # FastMCP's run() is a blocking call for stdio
    mcp_server.run()

def run_http_surface():
    """Run the Teams HTTP surface via uvicorn."""
    uvicorn.run(
        teams_app,
        host=settings.server_host,
        port=settings.server_port,
        log_level="info",
    )

def main():
    """Split entrypoint for MCP and HTTP surfaces."""
    parser = argparse.ArgumentParser(description="Agentic MS Teams MCP Server")
    parser.add_argument(
        "--mcp", 
        action="store_true", 
        help="Run as an MCP stdio server"
    )
    parser.add_argument(
        "--http", 
        action="store_true", 
        help="Run as the Teams HTTP surface"
    )
    
    args = parser.parse_args()

    if args.mcp:
        run_mcp_stdio()
    elif args.http:
        run_http_surface()
    else:
        # Default behavior if no flag is provided: provide help
        parser.print_help()
        sys.exit(0)

if __name__ == "__main__":
    main()
