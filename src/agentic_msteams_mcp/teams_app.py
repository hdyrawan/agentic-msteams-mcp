from fastapi import FastAPI, Request, HTTPException, Body
from typing import Dict, Any
from .asks.service import service as ask_service
from .asks.models import AskState
from .security import validate_inbound_secret
from .approvals.service import service as approval_service
from .approvals.models import ApprovalState

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
                return {"status": "error", "reason": "Missing required parameters: approval_id, decision, and sender_user_id are required"}

            if decision not in ["approved", "rejected"]:
                return {"status": "error", "reason": "Invalid decision value. Must be 'approved' or 'rejected'"}

            # Map string decision to ApprovalState enum
            target_state = ApprovalState.APPROVED if decision == "approved" else ApprovalState.REJECTED

            # Fetch existing approval to validate target user, state and expiration
            from .approvals.store import store as app_store
            approval = await app_store.get(approval_id)
            if not approval:
                return {"status": "error", "reason": f"Unknown approval ID: {approval_id}"}

            if approval.target_user_id != sender_user_id:
                return {"status": "error", "reason": "Sender user ID does not match the approved target user"}

            if approval.is_expired():
                return {"status": "error", "reason": "Approval has expired"}

            if approval.state != ApprovalState.PENDING:
                return {"status": "error", "reason": f"Approval is already in state: {approval.state}"}

            # Record the decision
            result = await approval_service.set_decision(approval_id, target_state, reason)
            if not result:
                return {"status": "error", "reason": "Failed to record approval decision"}

            return {
                "status": "received",
                "approval_id": approval_id,
                "decision": decision
            }

        # Logic for handling replies
        if "reply_to" in body:
            request_id = body["reply_to"]
            reply_text = body.get("text", "")
            target_user_id = body.get("target_user_id")
            tool_name = body.get("tool_name")
            requester_agent_id = body.get("requester_agent_id")

            if not all([target_user_id, tool_name, requester_agent_id]):
                return {
                    "status": "error",
                    "reason": "Missing security parameters: target_user_id, tool_name, or requester_agent_id are required for replies"
                }

            ask = await ask_service.set_reply(
                request_id=request_id,
                text=reply_text,
                target_user_id=target_user_id,
                tool_name=tool_name,
                requester_agent_id=requester_agent_id
            )
            if not ask:
                return {"status": "error", "reason": "Invalid request_id or authorization failure"}
            return {"status": "received", "request_id": request_id}

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
