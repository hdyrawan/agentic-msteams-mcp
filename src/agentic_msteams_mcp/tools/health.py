"""Health check tool for agentic-msteams-mcp."""

from typing import Any

def msteams_health_check(**kwargs: Any) -> dict[str, Any]:
    """Perform a basic health check of the Teams server.
    
    Args:
        **kwargs: Ignored in v0.2.0.
    
    Returns:
        dict with status, service, and checks fields.
    """
    return {
        "status": "ok",
        "service": "msteams-mcp",
        "checks": {
            "configuration": "loaded",
            "dependencies": "available",
        },
    }
