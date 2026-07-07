from typing import Any, Dict

# Import the real business logic
from .tools.health import msteams_health_check as _real_health_check 
from .notifications.models import NotificationRequest, NotificationResult, TargetType
from .notifications.service import DryRunNotificationSender, RealGraphNotificationSender, NotificationSender
from .policy.allowlist import is_target_allowed
from .audit.writer import write_audit_log
from .config import settings

# New Ask imports
from .asks.service import service as ask_service
from .asks.validation import UserAskRequest, UserReplyRequest
from .asks.models import AskState
from .approvals.service import service as approval_service
from .approvals.validation import UserApprovalRequest

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
    '''Send a controlled notification to an allowlisted Microsoft Teams target.'''
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
        placeholder_req = NotificationRequest.model_construct(
            target_id=target_id, target_type=target_type, title="VALIDATION_FAIL"
        )
        res = NotificationResult(
            status="error", target_type=TargetType.USER if target_type != "channel" else TargetType.CHANNEL, 
            target_id=target_id,
            delivered=False, dry_run=settings.msteams_notification_dry_run,
            reason=f"Validation failed: {str(e)}"
        )
        audit_id = write_audit_log(placeholder_req, res, event_type="notification")
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
        audit_id = write_audit_log(req, res, event_type="notification")
        return res.model_dump() | {"audit_id": audit_id}

    sender = get_notification_sender()
    res = await sender.send(req)
    audit_id = write_audit_log(req, res, event_type="notification")
    return res.model_dump() | {"audit_id": audit_id}

async def msteams_ask_user(
    target_user_id: str, 
    question: str, 
    correlation_id: str = None, 
    metadata: dict = None, 
    expires_in_seconds: int = 3600
) -> Dict[str, Any]:
    '''Ask a controlled question to an allowlisted Microsoft Teams user.'''
    try:
        req = UserAskRequest(
            target_user_id=target_user_id,
            question=question,
            correlation_id=correlation_id,
            metadata=metadata,
            expires_in_seconds=expires_in_seconds
        )
    except Exception as e:
        placeholder = UserAskRequest.model_construct(target_user_id=target_user_id, question="VALIDATION_FAIL")
        res_status = "error"
        reason = f"Validation failed: {str(e)}"
        audit_id = write_audit_log(placeholder, {"status": res_status, "reason": reason}, event_type="ask_creation")
        return {"status": "error", "reason": reason, "audit_id": audit_id}

    if not is_target_allowed(TargetType.USER, req.target_user_id):
        res_status = "denied"
        reason = "User not in allowlist"
        audit_id = write_audit_log(req, {"status": res_status, "reason": reason}, event_type="ask_creation")
        return {"status": "denied", "reason": reason, "audit_id": audit_id}

    ask = await ask_service.create_ask(
        target_user_id=req.target_user_id,
        question=req.question,
        correlation_id=req.correlation_id,
        metadata=req.metadata,
        expires_in_seconds=req.expires_in_seconds
    )
    audit_id = write_audit_log(ask, {"status": "success", "reason": "Ask created"}, event_type="ask_creation")
    return {
        "status": "success",
        "request_id": ask.request_id,
        "target_user_id": ask.target_user_id,
        "state": ask.state,
        "expires_at": ask.expires_at.isoformat(),
        "dry_run": settings.msteams_notification_dry_run,
        "audit_id": audit_id
    }

async def msteams_get_user_reply(request_id: str) -> Dict[str, Any]:
    '''Check the state of a requested user reply.'''
    try:
        req = UserReplyRequest(request_id=request_id)
    except Exception as e:
        # Now audited!
        placeholder = UserReplyRequest.model_construct(request_id=request_id)
        res_status = "error"
        reason = f"Validation failed: {str(e)}"
        audit_id = write_audit_log(placeholder, {"status": res_status, "reason": reason}, event_type="reply_lookup")
        return {"status": "error", "reason": reason, "audit_id": audit_id}

    state, reply_text = await ask_service.get_reply_status(req.request_id)
    
    # Audit the lookup result
    audit_id = write_audit_log(req, {"status": state, "reason": f"Reply check: {state}"}, event_type="reply_lookup")
    
    return {
        "status": "success",
        "request_id": request_id,
        "state": state,
        "reply": reply_text if state == AskState.ANSWERED else None,
        "audit_id": audit_id
    }

async def msteams_request_approval(
    target_user_id: str, 
    title: str, 
    description: str, 
    risk_level: str = None,
    action_fingerprint: str = None,
    correlation_id: str = None,
    metadata: dict = None,
    expires_in_seconds: int = 3600
) -> Dict[str, Any]:
    '''Request human approval for an action via an allowlisted Teams user.'''
    try:
        req = UserApprovalRequest(
            target_user_id=target_user_id,
            title=title,
            description=description,
            risk_level=risk_level,
            action_fingerprint=action_fingerprint,
            correlation_id=correlation_id,
            metadata=metadata,
            expires_in_seconds=expires_in_seconds
        )
    except Exception as e:
        # Audit validation failure
        placeholder = UserApprovalRequest.model_construct(target_user_id=target_user_id, title="VALIDATION_FAIL")
        res_status = "error"
        reason = f"Validation failed: {str(e)}"
        audit_id = write_audit_log(placeholder, {"status": res_status, "reason": reason}, event_type="approval_request")
        return {"status": "error", "reason": reason, "audit_id": audit_id}

    if not is_target_allowed(TargetType.USER, req.target_user_id):
        res_status = "denied"
        reason = "User not in allowlist"
        audit_id = write_audit_log(req, {"status": res_status, "reason": reason}, event_type="approval_request")
        return {"status": "denied", "reason": reason, "audit_id": audit_id}

    approval = await approval_service.create_approval(
        target_user_id=req.target_user_id,
        title=req.title,
        description=req.description,
        risk_level=req.risk_level,
        action_fingerprint=req.action_fingerprint,
        correlation_id=req.correlation_id,
        metadata=req.metadata,
        expires_in_seconds=req.expires_in_seconds
    )
    audit_id = write_audit_log(approval, {"status": "success", "reason": "Approval created"}, event_type="approval_request")
    return {
        "status": "success",
        "approval_id": approval.approval_id,
        "state": approval.state,
        "expires_at": approval.expires_at.isoformat(),
        "dry_run": settings.msteams_notification_dry_run,
        "audit_id": audit_id
    }

async def msteams_get_approval(approval_id: str) -> Dict[str, Any]:
    '''Check the current state of a requested approval.'''
    try:
        # Simple validation for request ID
        if not approval_id or not approval_id.strip():
            raise ValueError("Approval ID cannot be empty")
    except Exception as e:
        placeholder = {"approval_id": approval_id}
        res_status = "error"
        reason = f"Validation failed: {str(e)}"
        audit_id = write_audit_log(placeholder, {"status": res_status, "reason": reason}, event_type="approval_lookup")
        return {"status": "error", "reason": reason, "audit_id": audit_id}

    state, reason = await approval_service.get_approval_status(approval_id)
    audit_id = write_audit_log({"approval_id": approval_id}, {"status": state, "reason": f"Approval check: {state}"}, event_type="approval_lookup")
    return {
        "status": "success",
        "approval_id": approval_id,
        "state": state,
        "reason": reason,
        "audit_id": audit_id
    }

from mcp.server.fastmcp import FastMCP as _FastMCP


def _register_tools(mcp: _FastMCP) -> None:
    @mcp.tool(name="msteams_health_check", description="Check Microsoft Teams server health")
    async def _health() -> Dict[str, Any]:
        return _real_health_check(**{})

    @mcp.tool(name="msteams_send_notification", description="Send a controlled notification to an allowlisted Teams target")
    async def _notify(target_type: str, target_id: str, title: str, message: str, severity: str, correlation_id: str = None, metadata: dict = None) -> Dict[str, Any]:
        return await msteams_send_notification(target_type, target_id, title, message, severity, correlation_id, metadata)

    @mcp.tool(name="msteams_ask_user", description="Ask a controlled question to an allowlisted Teams user")
    async def _ask(target_user_id: str, question: str, correlation_id: str = None, metadata: dict = None, expires_in_seconds: int = 3600) -> Dict[str, Any]:
        return await msteams_ask_user(target_user_id, question, correlation_id, metadata, expires_in_seconds)

    @mcp.tool(name="msteams_get_user_reply", description="Check the state of a requested user reply")
    async def _get_reply(request_id: str) -> Dict[str, Any]:
        return await msteams_get_user_reply(request_id)

    @mcp.tool(name="msteams_request_approval", description="Request human approval for an action via an allowlisted Teams user")
    async def _request_approval(target_user_id: str, title: str, description: str, risk_level: str = None, action_fingerprint: str = None, correlation_id: str = None, metadata: dict = None, expires_in_seconds: int = 3600) -> Dict[str, Any]:
        return await msteams_request_approval(target_user_id, title, description, risk_level, action_fingerprint, correlation_id, metadata, expires_in_seconds)

    @mcp.tool(name="msteams_get_approval", description="Check the current state of a requested approval")
    async def _get_approval(approval_id: str) -> Dict[str, Any]:
        return await msteams_get_approval(approval_id)

mcp_server = _FastMCP(name="agentic-msteams-mcp", host="127.0.0.1", port=8000)
_register_tools(mcp_server)
