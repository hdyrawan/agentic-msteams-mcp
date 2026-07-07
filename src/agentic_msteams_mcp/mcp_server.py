from typing import Any, Dict

# Import the real business logic
from .tools.health import msteams_health_check as _real_health_check 
from .notifications.models import NotificationRequest, NotificationResult
from .notifications.service import DryRunNotificationSender, NotificationSender
from .policy.allowlist import is_target_allowed
from .audit.writer import write_audit_log
from .config import settings

# Instance resolution based on config
def get_notification_sender() -> NotificationSender:
    if settings.msteams_notification_dry_run:
        return DryRunNotificationSender()
    # In v0.2.0, we only have dry-run implemented. 
    # If configured’False’, this would be where a real sender is returned.
    return DryRunNotificationSender()

async def msteams_send_notification(
    target_type: str, 
    target_id: str, 
    title: str, 
    message: str, 
    severity: str, 
    correlation_id: str = None, 
    metadata: dict = None
) -> Dict[str, Any]:
    '''
    Send a controlled notification to an allowlisted Microsoft Teams target.
    '''
    try:
        req = NotificationRequest(
            target_type=target_type,
            target_id=target_id,
            title=title,
            message=message,
            severity=severity,
            correlation_id=correlation_id,
            metadata=metadata
        )
    except Exception as e:
        return {"status": "error", "reason": f"Validation failed: {str(e)}"}

    if not is_target_allowed(req.target_type, req.target_id):
        result = NotificationResult(
            status="denied",
            target_type=req.target_type,
            target_id=req.target_id,
            delivered=False,
            dry_run=settings.msteams_notification_dry_run, 
            reason="Target not in allowlist"
        )
        write_audit_log(req, result)
        return result.model_dump()

    sender = get_notification_sender()
    result = await sender.send(req)
    
    audit_id = write_audit_log(req, result)
    final_result = result.model_copy(update={"audit_id": audit_id})
    return final_result.model_dump()

from mcp.server.fastmcp import FastMCP as _FastMCP

def _register_tools(mcp: _FastMCP) -> None:
    '''Register v0.2.0 tools on the given MCP server.'''

    @mcp.tool(
        name="msteams_health_check",
        description="Check Microsoft Teams server health"
    )
    async def _health() -> Dict[str, Any]:
        return _real_health_check(**{})

    @mcp.tool(
        name="msteams_send_notification",
        description="Send a controlled notification to an allowlisted Teams target"
    )
    async def _notify(
        target_type: str, 
        target_id: str, 
        title: str, 
        message: str, 
        severity: str, 
        correlation_id: str = None, 
        metadata: dict = None
    ) -> Dict[str, Any]:
        return await msteams_send_notification(
            target_type=target_type, 
            target_id=target_id, 
            title=title, 
            message=message, 
            severity=severity, 
            correlation_id=correlation_id, 
            metadata=metadata
        )

mcp_server = _FastMCP(
    name="agentic-msteams-mcp",
    host="127.0.0.1",
    port=8000,
)

_register_tools(mcp_server)
