from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

class ApprovalState(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    NOT_FOUND = "not_found"

class UserApproval(BaseModel):
    approval_id: str
    target_user_id: str
    title: str
    description: str
    risk_level: Optional[str] = None  # low, medium, high, critical
    action_fingerprint: Optional[str] = None
    correlation_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    expires_at: datetime
    state: ApprovalState = ApprovalState.PENDING
    decision_made_at: Optional[datetime] = None
    reason: Optional[str] = None

    def is_expired(self) -> bool:
        return datetime.now().timestamp() > self.expires_at.timestamp()
