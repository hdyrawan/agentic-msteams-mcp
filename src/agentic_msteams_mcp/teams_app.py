from fastapi import FastAPI, Request, HTTPException, Body
from typing import Dict, Any
from .asks.service import service as ask_service
from .asks.models import AskState

teams_app = FastAPI(
    title="Teams Bot Endpoint",
    description="HTTP endpoint for Microsoft Teams bot messages"
)

@teams_app.post("/api/messages")
async def handle_teams_message(request: Request) -> Dict[str, Any]:
    """Handle incoming messages from Microsoft Teams."""
    try:
        body = await request.json()
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
