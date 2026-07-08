import pytest
import asyncio
from agentic_msteams_mcp.mcp_server import msteams_request_approval, msteams_get_approval
from agentic_msteams_mcp.config import settings
from agentic_msteams_mcp.approvals.models import ApprovalState

def run_async(coro):
    return asyncio.run(coro)

@pytest.fixture(autouse=True)
def setup_test_state(tmp_path):
    from agentic_msteams_mcp.approvals.store import store as approval_store
    settings.msteams_allowed_user_ids = ["test-user"]
    settings.msteams_notification_dry_run = True
    settings.msteams_audit_log_path = str(tmp_path / "approvals_audit.log")
    approval_store._approvals = {}
    (tmp_path / "approvals_audit.log").write_text("")
    yield

def test_request_approval_allowed():
    res = run_async(msteams_request_approval("test-user", "Title", "Description"))
    assert res["status"] == "success"
    assert "approval_id" in res
    assert "state" in res
    assert "expires_at" in res
    assert "audit_id" in res

def test_request_approval_denied():
    res = run_async(msteams_request_approval("hacker", "Title", "Description"))
    assert res["status"] == "denied"
    assert "audit_id" in res

def test_request_approval_whitespace_validation():
    # Empty title
    res = run_async(msteams_request_approval("test-user", "  ", "Description"))
    assert res["status"] == "error"
    assert "audit_id" in res
    
    # Empty description
    res = run_async(msteams_request_approval("test-user", "Title", "  "))
    assert res["status"] == "error"
    assert "audit_id" in res

def test_request_approval_invalid_risk():
    # Assuming risk_level has specific allowed values (e.g., low, medium, high, critical)
    # If the validation is via Pydantic enum/literal, this should fail.
    res = run_async(msteams_request_approval("test-user", "Title", "Description", risk_level="super-danger"))
    assert res["status"] == "error"
    assert "audit_id" in res

def test_get_approval_pending():
    # Create one first
    req_res = run_async(msteams_request_approval("test-user", "Title", "Description"))
    aid = req_res["approval_id"]
    
    res = run_async(msteams_get_approval(aid))
    assert res["status"] == "success"
    assert res["state"] == "pending"

def test_get_approval_not_found():
    res = run_async(msteams_get_approval("ghost-id"))
    assert res["status"] == "success" # The tool returns success but state is NOT_FOUND
    assert res["state"] == "not_found"

def test_approval_audit_no_body():
    # Approval description should not be in audit logs
    secret_desc = "SECRET_APPROVAL_BODY_12345"
    run_async(msteams_request_approval("test-user", "Title", secret_desc))
    
    with open(settings.msteams_audit_log_path, "r") as f:
        logs = f.read()
        assert secret_desc not in logs
