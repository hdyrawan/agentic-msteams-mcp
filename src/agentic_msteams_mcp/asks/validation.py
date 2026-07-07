from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, field_validator
from .models import AskState

class UserAskRequest(BaseModel):
    target_user_id: str = Field(..., min_length=1)
    question: str = Field(..., min_length=1, max_length=2000)
    correlation_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    expires_in_seconds: Optional[int] = Field(default=3600, ge=60, le=86400)

    @field_validator("question", mode="before")
    @classmethod
    def strip_whitespace(cls, v):
        if isinstance(v, str):
            stripped = v.strip()
            if not stripped:
                raise ValueError("Question cannot be whitespace-only")
            return stripped
        return v

class UserReplyRequest(BaseModel):
    request_id: str = Field(..., min_length=1)
