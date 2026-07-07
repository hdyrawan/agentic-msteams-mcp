from typing import Optional, Dict, Any
import uuid
from datetime import datetime, timedelta
from .models import UserAsk, AskState
from .store import store

class AskService:
    """Business logic for managing user asks."""
    
    async def create_ask(
        self, 
        target_user_id: str, 
        question: str, 
        correlation_id: Optional[str] = None, 
        metadata: Optional[Dict[str, Any]] = None, 
        expires_in_seconds: int = 3600
    ) -> UserAsk:
        request_id = str(uuid.uuid4())
        now = datetime.now()
        
        ask = UserAsk(
            request_id=request_id,
            target_user_id=target_user_id,
            question=question,
            correlation_id=correlation_id,
            metadata=metadata,
            created_at=now,
            expires_at=now + timedelta(seconds=expires_in_seconds),
            state=AskState.PENDING
        )
        await store.save(ask)
        return ask

    async def get_reply_status(self, request_id: str) -> tuple[AskState, Optional[str]]:
        ask = await store.get(request_id)
        if not ask:
            return AskState.NOT_FOUND, None
        
        if ask.is_expired():
            ask.state = AskState.EXPIRED
            await store.save(ask)
            return AskState.EXPIRED, None
            
        return ask.state, ask.reply_text

    async def set_reply(self, request_id: str, text: str) -> Optional[UserAsk]:
        ask = await store.update_state(request_id, AskState.ANSWERED, reply=text)
        if ask:
            ask.reply_received_at = datetime.now()
        return ask

service = AskService()
