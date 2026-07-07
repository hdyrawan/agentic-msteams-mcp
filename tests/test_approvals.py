import pytest
from datetime import datetime, timedelta, timezone
from src.agentic_msteams_mcp.approvals.service import service as approval_service
from src.agentic_msteams_mcp.approvals.store import store as approval_store
from src.agentic_msteams_mcp.approvals.models import ApprovalState
import asyncio

@pytest.fixture(autouse=True)
def clear_store():
    approval_store._approvals = {}
    yield

@pytest.mark.asyncio
async def test_approval_lifecycle():
    target = "user-1"
    title = "Critical Action"
    desc = "Delete Production DB"
    
    app = await approval_service.create_approval(
        target_user_id=target, title=title, description=desc, risk_level="critical"
    )
    
    assert app.approval_id.startswith("app-")
    assert app.state == ApprovalState.PENDING
    
    # Check get status
    state, reason = await approval_service.get_approval_status(app.approval_id)
    assert state == ApprovalState.PENDING
    
    # Set to approved
    await approval_service.set_decision(app.approval_id, ApprovalState.APPROVED, "Looks good")
    state, reason = await approval_service.get_approval_status(app.approval_id)
    assert state == ApprovalState.APPROVED
    assert reason == "Looks good"

@pytest.mark.asyncio
async def test_approval_expired():
    target = "user-1"
    app = await approval_service.create_approval(
        target_user_id=target, title="Test", description="Test", expires_in_seconds=-60
    )
    
    state, reason = await approval_service.get_approval_status(app.approval_id)
    assert state == ApprovalState.EXPIRED

@pytest.mark.asyncio
async def test_approval_not_found():
    state, reason = await approval_service.get_approval_status("non-existent")
    assert state == ApprovalState.NOT_FOUND

@pytest.mark.asyncio
async def test_decision_immutability():
    target = "user-1"
    app = await approval_service.create_approval(
        target_user_id=target, title="Test", description="Test"
    )
    await approval_service.set_decision(app.approval_id, ApprovalState.REJECTED, "No")
    
    # Try to change it to APPROVED
    updated = await approval_service.set_decision(app.approval_id, ApprovalState.APPROVED, "Yes")
    assert updated.state == ApprovalState.REJECTED
