from fastapi import FastAPI, Request, HTTPException, Body
from typing import Dict, Any
from .asks.service import service as ask_service
from .asks.models import AskState
from .security import validate_inbound_secret
from .approvals.service import service as approval_service
from .approvals.models import ApprovalState
from .audit.writer import write_audit_log

teams_app = FastAPI(
    title="Teams Bot Endpoint",
    description="HTTP endpoint for Microsoft Teams bot messages"
)

@teams_app.post("/api/messages")
async def handle_teams_message(request: Request) -> Dict[str, Any]:
    """Handle incoming messages from Microsoft Teams."""
    # 1. Inbound Secret Validation
    provided_secret = request.headers.get("X-MSTEAMS-MCP-SECRET")
    is_valid, auth_msg = validate_inbound_secret(provided_secret)
    if not is_valid:
        raise HTTPException(status_code=401, detail=auth_msg)

    try:
        body = await request.json()

        # 2. Approval Decision Callback
        if "approval_id" in body:
            approval_id = body["approval_id"]
            decision = body.get("decision")
            sender_user_id = body.get("sender_user_id")
            reason = body.get("reason")

            if not all([approval_id, decision, sender_user_id]):
                res = {"status": "error", "reason": "Missing required parameters: approval_id, decision, and sender_user_id are required"}
                write_audit_log(body, res, event_type="approval_callback")
                return res

            if decision not in ["approved", "rejected"]:
                res = {"status": "error", "reason": "Invalid decision value. Must be 'approved' or 'rejected'"}
                write_audit_log(body, res, event_type="approval_callback")
                return res

            # Map string decision to ApprovalState enum
            target_state = ApprovalState.APPROVED if decision == "approved" else ApprovalState.REJECTED

            # Fetch existing approval to validate target user, state and expiration
            from .approvals.store import store as app_store
            approval = await app_store.get(approval_id)
            if not approval:
                res = {"status": "error", "reason": f"Unknown approval ID: {approval_id}"}
                write_audit_log(body, res, event_type="approval_callback")
                return res

            if approval.target_user_id != sender_user_id:
                res = {"status": "error", "reason": "Sender user ID does not match the approved target user"}
                write_audit_log(body, res, event_type="approval_callback")
                return res

            if approval.is_expired():
                # Persist EXPIRED state before returning error
                await app_store.update_state(approval_id, ApprovalState.EXPIRED)
                res = {"status": "error", "reason": "Approval has expired"}
                write_audit_log(body, res, event_type="approval_callback")
                return res

            if approval.state != ApprovalState.PENDING:
                res = {"status": "error", "reason": f"Approval is already in state: {approval.state}"}
                write_audit_log(body, res, event_type="approval_callback")
                return res

            # Record the decision
            result = await approval_service.set_decision(approval_id, target_state, reason)
            if not result:
                res = {"status": "error", "reason": "Failed to record approval decision"}
                write_audit_log(body, res, event_type="approval_callback")
                return res

            res = {
                "status": "received",
                "approval_id": approval_id,
                "decision": decision
            }
            write_audit_log(body, res, event_type="approval_callback")
            return res

        # Logic for handling replies
        if "reply_to" in body:
            request_id = body["reply_to"]
            reply_text = body.get("text", "")
            target_user_id = body.get("target_user_id")
            tool_name = body.get("tool_name")
            requester_agent_id = body.get("requester_agent_id")

            if not all([target_user_id, tool_name, requester_agent_id]):
                res = {
                    "status": "error",
                    "reason": "Missing security parameters: target_user_id, tool_name, or requester_agent_id are required for replies"
                }
                write_audit_log(body, res, event_type="reply_callback")
                return res

            ask = await ask_service.set_reply(
                request_id=request_id,
                text=reply_text,
                target_user_id=target_user_id,
                tool_name=tool_name,
                requester_agent_id=requester_agent_id
            )
            if not ask:
                res = {"status": "error", "reason": "Invalid request_id or authorization failure"}
                write_audit_log(body, res, event_type="reply_callback")
                return res

            res = {"status": "received", "request_id": request_id}
            write_audit_log(body, res, event_type="reply_callback")
            return res

        return {
            "status": "received",
            "message_id": body.get("id"),
            "timestamp": body.get("timestamp")
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing message: {str(e)}")

@teams_app.get("/health")
async def teams_health() -> Dict[str, Any]:
    return {"status": "healthy", "service": "teams-bot"}
