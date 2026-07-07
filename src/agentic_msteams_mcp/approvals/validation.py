from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator
from .models import ApprovalState

class UserApprovalRequest(BaseModel):
    target_user_id: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1, max_length=5000)
    risk_level: Optional[str] = Field(default=None, pattern=r"^(low|medium|high|critical)$")
    action_fingerprint: Optional[str] = None
    correlation_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    expires_in_seconds: Optional[int] = Field(default=3600, ge=60, le=86400)

    @field_validator("title", "description", mode="before")
    @classmethod
    def strip_whitespace(cls, v):
        if isinstance(v, str):
            stripped = v.strip()
            if not stripped:
                raise ValueError("Field cannot be whitespace-only")
            return stripped
        return v
