from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, field_validator, field_validator as validator
from .models import AskState
import secrets

class UserAskRequest(BaseModel):
    target_user_id: str = Field(..., min_length=1)
    question: str = Field(..., min_length=1, max_length=2000)
    correlation_id: Optional[str] = Field(default=None)
    metadata: Optional[Dict[str, Any]] = Field(default=None)
    expires_in_seconds: int = Field(default=3600, ge=60, le=86400)

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
    target_user_id: str = Field(..., min_length=1)
    tool_name: str = Field(..., min_length=1)
    requester_agent_id: str = Field(..., min_length=1)

    @validator("target_user_id", "tool_name", "requester_agent_id")
    def strip_whitespace(cls, v):
        if isinstance(v, str):
            stripped = v.strip()
            if not stripped:
                raise ValueError("Identifier cannot be whitespace-only")
            return stripped
        return v

    @validator("request_id")
    @classmethod
    def validate_request_id(cls, v):
        """Ensure request_id is not empty and is a valid base64 string"""
        v = v.strip() if isinstance(v, str) else v
        if not v:
            raise ValueError("Request ID cannot be empty")
        if len(v) < 20:  # Reasonable minimum length for security
            raise ValueError("Request ID too short for security")
        return v
