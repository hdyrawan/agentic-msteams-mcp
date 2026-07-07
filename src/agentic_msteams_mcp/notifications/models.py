from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator
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

    @field_validator("title", "message", mode="before")
    @classmethod
    def strip_and_validate(cls, v):
        if isinstance(v, str):
            stripped = v.strip()
            if not stripped:
                raise ValueError("Field cannot be whitespace-only")
            return stripped
        return v

class NotificationResult(BaseModel):
    status: str
    notification_id: Optional[str] = None
    target_type: TargetType
    target_id: str
    delivered: bool
    dry_run: bool
    reason: Optional[str] = None
    audit_id: Optional[str] = None
