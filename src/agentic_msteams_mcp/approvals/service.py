import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, Tuple
from .models import UserApproval, ApprovalState
from .store import store

class ApprovalService:
    """Business logic for managing agnostic human approvals."""

    async def create_approval(
        self, 
        target_user_id: str, 
        title: str, 
        description: str, 
        risk_level: Optional[str] = None,
        action_fingerprint: Optional[str] = None,
        correlation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        expires_in_seconds: int = 3600
    ) -> UserApproval:
        approval_id = f"app-{str(uuid.uuid4())[:12]}"
        now = datetime.now(timezone.utc)
        
        approval = UserApproval(
            approval_id=approval_id,
            target_user_id=target_user_id,
            title=title,
            description=description,
            risk_level=risk_level,
            action_fingerprint=action_fingerprint,
            correlation_id=correlation_id,
            metadata=metadata,
            created_at=now,
            expires_at=now + timedelta(seconds=expires_in_seconds),
            state=ApprovalState.PENDING
        )
        await store.save(approval)
        return approval

    async def get_approval_status(self, approval_id: str) -> Tuple[ApprovalState, Optional[str]]:
        approval = await store.get(approval_id)
        if not approval:
            return ApprovalState.NOT_FOUND, None
        
        if approval.is_expired():
            approval.state = ApprovalState.EXPIRED
            await store.save(approval)
            return ApprovalState.EXPIRED, None
            
        return approval.state, approval.reason

    async def set_decision(self, approval_id: str, state: ApprovalState, reason: Optional[str] = None) -> Optional[UserApproval]:
        """Internal method to move approval out of pending. Used for test injection or Teams callback."""
        now = datetime.now(timezone.utc)
        approval = await store.get(approval_id)
        if not approval:
            return None
            
        if approval.state != ApprovalState.PENDING:
            # Cannot change decision once made or expired
            return approval

        approval.state = state
        approval.reason = reason
        approval.decision_made_at = now
        
        await store.save(approval)
        return approval

service = ApprovalService()
