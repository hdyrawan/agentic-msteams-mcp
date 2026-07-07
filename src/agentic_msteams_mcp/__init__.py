"""Main module for agentic-msteams-mcp."""

from fastapi import FastAPI

__version__: str = "0.2.0"

# The app is now consolidated in teams_app.py to avoid duplication and confusion.
# We import it here to maintain the entrypoint used by uvicorn if necessary,
# although main.py provides the primary logic for splitting servers.
from .teams_app import teams_app as app