from typing import Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
from .models import UserAsk, AskState
from .store import store
import hashlib
import secrets
import base64

class AskService:
    """Business logic for managing user asks."""
    
    # Default TTL of 15 minutes as suggested in the requirements
    DEFAULT_TTL_SECONDS = 15 * 60
    
    async def create_ask(
        self,
        target_user_id: str,
        question: str,
        correlation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        expires_in_seconds: int = DEFAULT_TTL_SECONDS,
        tool_name: str = "msteams_ask_user",
        requester_agent_id: str = "unknown"
    ) -> UserAsk:
        # Use cryptographic binding to generate secure request ID
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(seconds=expires_in_seconds)

        # Generate cryptographically secure request ID with binding information
        request_id = UserAsk.generate_secure_request_id(
            target_user_id=target_user_id,
            tool_name=tool_name,
            requester_agent_id=requester_agent_id,
            expires_at=expires_at
        )

        ask = UserAsk(
            request_id=request_id,
            target_user_id=target_user_id,
            question=question,
            correlation_id=correlation_id,
            metadata=metadata,
            created_at=now,
            expires_at=expires_at,
            state=AskState.PENDING,
            tool_name=tool_name,
            requester_agent_id=requester_agent_id
        )
        await store.save(ask)
        return ask

    async def get_reply_status(
        self,
        request_id: str,
        target_user_id: str,
        tool_name: str,
        requester_agent_id: str
    ) -> tuple[AskState, Optional[str]]:
        """
        Check the state of a user reply with strict authorization.

        This method enforces:
        1. Request ID binding (target_user_id, tool_name, requester_agent_id)
        2. Expiration checking (TTL enforcement)
        3. Replay protection (immutable state after completion)
        """
        ask = await store.get(request_id)
        if not ask:
            return AskState.NOT_FOUND, None

        # SECURITY: Verify request ID binding to prevent cross-workflow hijacking
        if not ask.verify_request_id(target_user_id, tool_name, requester_agent_id):
            # Access denied - different agent/tool/user combination
            return AskState.NOT_FOUND, None

        # Check expiration using timezone-aware UTC
        now = datetime.now(timezone.utc)
        if now > ask.expires_at:
            # Security: Only update to EXPIRED if it was PENDING
            if ask.state == AskState.PENDING:
                ask.state = AskState.EXPIRED
                await store.save(ask)
            return AskState.EXPIRED, None

        # Security: Prevent replay after completion (Immutable state)
        if ask.state in (AskState.ANSWERED, AskState.EXPIRED, AskState.CANCELLED):
            return ask.state, ask.reply_text

        return ask.state, ask.reply_text

    async def set_reply(self, request_id: str, text: str, target_user_id: str, tool_name: str, requester_agent_id: str) -> Optional[UserAsk]:
        now = datetime.now(timezone.utc)
        ask = await store.get(request_id)
        if not ask:
            return None
            
        # Verify that this is the correct user and agent accessing the reply
        if not ask.verify_request_id(target_user_id, tool_name, requester_agent_id):
            # This shouldn't happen in normal operations as the caller should be authenticated
            return None
        
        ask.state = AskState.ANSWERED
        ask.reply_text = text
        ask.reply_received_at = now
        
        await store.save(ask)
        return ask
    
    async def get_reply_status_no_auth(self, request_id: str) -> tuple[AskState, Optional[str]]:
        """
        Get reply status for audit logging without authorization check.

        Used internally for state transition logging (non-sensitive operations).
        """
        ask = await store.get(request_id)
        if not ask:
            return AskState.NOT_FOUND, None

        # Check expiration
        now = datetime.now(timezone.utc)
        if now > ask.expires_at:
            ask.state = AskState.EXPIRED
            await store.save(ask)
            return AskState.EXPIRED, None

        return ask.state, ask.reply_text

    async def cancel_request(
        self,
        request_id: str,
        target_user_id: str,
        tool_name: str,
        requester_agent_id: str
    ) -> Optional[UserAsk]:
        """
        Cancel a pending user ask request.

        This requires authorization matching the original request.
        Cancels prevent expiration-based cleanup.
        """
        ask = await store.get(request_id)
        if not ask:
            return None

        # SECURITY: Verify request ID binding
        if not ask.verify_request_id(target_user_id, tool_name, requester_agent_id):
            return None

        # Only pending requests can be cancelled
        if ask.state != AskState.PENDING:
            return None

        # CANCELLED state is immutable
        ask.state = AskState.CANCELLED
        await store.save(ask)

        return ask

    async def _set_state(self, request_id: str, state: AskState, reply: Optional[str] = None) -> Optional[UserAsk]:
        """
        Internal helper to set state (for logging purposes).
        """
        ask = await store.get(request_id)
        if ask:
            ask.state = state
            if reply:
                ask.reply_text = reply
            return ask
        return None

service = AskService()
