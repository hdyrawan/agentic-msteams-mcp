from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from enum import Enum

class TargetType(str, Enum):
    USER = "user"
    CHANNEL = "channel"

class Severity(str, Enum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class NotificationRequest(BaseModel):
    target_type: TargetType
    target_id: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1, max_length=255)
    message: str = Field(..., min_length=1, max_length=4000)
    severity: Severity
    correlation_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    @validator("title", "message")
    def sanitize_text(cls, v):
        return v.strip()

class NotificationResult(BaseModel):
    status: str
    notification_id: Optional[str] = None
    target_type: TargetType
    target_id: str
    delivered: bool
    dry_run: bool
    reason: Optional[str] = None
    audit_id: Optional[str] = None
