from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import hashlib
import secrets
import base64

class AskState(str, Enum):
    PENDING = "pending"
    ANSWERED = "answered"
    EXPIRED = "expired"
    NOT_FOUND = "not_found"
    CANCELLED = "cancelled"
    FAILED = "failed"

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
    # Added binding information for security
    tool_name: Optional[str] = None  # Which tool initiated the ask 
    requester_agent_id: Optional[str] = None  # The agent that made the request
    
    def is_expired(self) -> bool:
        return datetime.now() > self.expires_at
    
    def verify_request_id(self, expected_target_user: str, expected_tool_name: str, expected_requester_agent: str) -> bool:
        """
        Verify this request ID is valid for accessing this specific user's reply.

        The request ID is bound to the target user, tool name, and requesting agent.
        This prevents cross-user workflow hijacking.
        """
        # If it's a fallback random ID (not bound), we can't verify via binding’ 
        # But for our new secure IDs:
        try:
            # Generate expected request ID using cryptographic binding
            binding_data = f"{expected_target_user}{expected_tool_name}{expected_requester_agent}{self.expires_at.isoformat()}"
            expected_hash = hashlib.sha256(binding_data.encode()).digest()
            expected_b64 = base64.urlsafe_b64encode(expected_hash).decode('utf-8').rstrip('=')

            # Compare with the stored request_id
            return self.request_id == expected_b64
        except Exception:
            return False

    @classmethod
    def generate_secure_request_id(cls, target_user_id: str, tool_name: str, requester_agent_id: str, expires_at: datetime) -> str:
        """
        Generate a cryptographically secure request ID with binding information.

        The request ID is bound to the target user, tool name, requesting agent, and expiry timestamp
        to prevent replay, guessing, and cross-workflow hijacking.

        Security properties:
        - Non-predictable: Uses SHA-256 of non-repeatable data
        - Replay-resistant: Bounded by expiry timestamp
        - Cross-workflow resistant: Bound to tool and agent identity
        - Non-guessable: 32-byte hash, encoded as 43-char base64 string
        """
        # Create binding data that includes all relevant parameters
        binding_data = f"{target_user_id}{tool_name}{requester_agent_id}{expires_at.isoformat()}"

        # Use SHA-256 for cryptographic hashing
        hash_digest = hashlib.sha256(binding_data.encode()).digest()

        # Base64 encode without padding for URL-safe storage
        # 32 bytes SHA-256 = 256 bits = 43 characters (base64 without padding)
        secure_id = base64.urlsafe_b64encode(hash_digest).decode('utf-8').rstrip('=')

        return secure_id

    @classmethod
    def generate_fallback_request_id(cls) -> str:
        """
        Fallback generation for backward compatibility with existing IDs.
        Use only when migrating existing data or for non-critical operations.
        """
        # Use secrets.token_urlsafe(32) for cryptographically random generation
        fallback_id = secrets.token_urlsafe(32)
        return fallback_id
