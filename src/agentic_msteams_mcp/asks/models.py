from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

class AskState(str, Enum):
    PENDING = "pending"
    ANSWERED = "answered"
    EXPIRED = "expired"
    NOT_FOUND = "not_found"

class UserAsk(BaseModel):
    request_id: str
    target_user_id: str
    question: str
    correlation_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    expires_at: datetime
    state: AskState = AskState.PENDING
    reply_text: Optional[str] = None
    reply_received_at: Optional[datetime] = None

    def is_expired(self) -> bool:
        return datetime.now() > self.expires_at
