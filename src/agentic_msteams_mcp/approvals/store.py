from typing import Dict, Optional
from .models import UserApproval

class ApprovalStore:
    """In-memory store for human approvals (v0.4.0).
    Note: Restarts clear all pending approvals."""
    def __init__(self):
        self._approvals: Dict[str, UserApproval] = {}

    async def save(self, approval: UserApproval) -> None:
        self._approvals[approval.approval_id] = approval

    async def get(self, approval_id: str) -> Optional[UserApproval]:
        return self._approvals.get(approval_id)

    async def update_state(self, approval_id: str, state: str, reason: Optional[str] = None) -> Optional[UserApproval]:
        approval = await self.get(approval_id)
        if approval:
            approval.state = state
            if reason:
                approval.reason = reason
            return approval
        return None

store = ApprovalStore()
