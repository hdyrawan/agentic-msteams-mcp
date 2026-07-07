from typing import Any, Dict

# Import the real business logic
from .tools.health import msteams_health_check as _real_health_check 
from .notifications.models import NotificationRequest, NotificationResult, TargetType
from .notifications.service import DryRunNotificationSender, RealGraphNotificationSender, NotificationSender
from .policy.allowlist import is_target_allowed
from .audit.writer import write_audit_log
from .config import settings

def get_notification_sender() -> NotificationSender:
    if settings.msteams_notification_dry_run:
        return DryRunNotificationSender()
    return RealGraphNotificationSender()

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
    # Use a temporary variable for audit logic consistency
    audit_res = None
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
        # Audit validation failure
        placeholder_req = NotificationRequest.model_construct(
            target_id=target_id, target_type=target_type, title="VALIDATION_FAIL"
        )
        res = NotificationResult(
            status="error", target_type=TargetType.USER if target_type != "channel" else TargetType.CHANNEL, 
            target_id=target_id,
            delivered=False, dry_run=settings.msteams_notification_dry_run,
            reason=f"Validation failed: {str(e)}"
        )
        audit_id = write_audit_log(placeholder_req, res)
        return {"status": "error", "reason": f"Validation failed: {str(e)}", "audit_id": audit_id}

    if not is_target_allowed(req.target_type, req.target_id):
        res = NotificationResult(
            status="denied",
            target_type=req.target_type,
            target_id=req.target_id,
            delivered=False,
            dry_run=settings.msteams_notification_dry_run, 
            reason="Target not in allowlist"
        )
        audit_id = write_audit_log(req, res)
        return res.model_dump() | {"audit_id": audit_id}

    sender = get_notification_sender()
    res = await sender.send(req)
    audit_id = write_audit_log(req, res)
    
    return res.model_dump() | {"audit_id": audit_id}

from mcp.server.fastmcp import FastMCP as _FastMCP

def _register_tools(mcp: _FastMCP) -> None:
    @mcp.tool(name="msteams_health_check", description="Check Microsoft Teams server health")
    async def _health() -> Dict[str, Any]:
        return _real_health_check(**{})

    @mcp.tool(name="msteams_send_notification", description="Send a controlled notification to an allowlisted Teams target")
    async def _notify(target_type: str, target_id: str, title: str, message: str, severity: str, correlation_id: str = None, metadata: dict = None) -> Dict[str, Any]:
        return await msteams_send_notification(target_type, target_id, title, message, severity, correlation_id, metadata)

mcp_server = _FastMCP(name="agentic-msteams-mcp", host="127.0.0.1", port=8000)
_register_tools(mcp_server)
