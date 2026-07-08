import pytest
import asyncio
from fastapi.testclient import TestClient
from agentic_msteams_mcp.mcp_server import msteams_request_approval, msteams_get_approval
from agentic_msteams_mcp.config import settings
from agentic_msteams_mcp.approvals.models import ApprovalState
from agentic_msteams_mcp.teams_app import teams_app

client = TestClient(teams_app)

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
    # Also set the shared secret for inbound auth tests
    settings.msteams_require_inbound_auth = True
    settings.msteams_inbound_shared_secret = "test-secure-secret"
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
    res = run_async(msteams_request_approval("test-user", "Title", "Description", risk_level="super-danger"))
    assert res["status"] == "error"
    assert "audit_id" in res

def test_get_approval_pending():
    req_res = run_async(msteams_request_approval("test-user", "Title", "Description"))
    aid = req_res["approval_id"]

    res = run_async(msteams_get_approval(aid))
    assert res["status"] == "success"
    assert res["state"] == "pending"

def test_get_approval_not_found():
    res = run_async(msteams_get_approval("ghost-id"))
    assert res["status"] == "success"
    assert res["state"] == "not_found"

def test_approval_audit_no_body():
    secret_desc = "SECRET_APPROVAL_BODY_12345"
    run_async(msteams_request_approval("test-user", "Title", secret_desc))

    # Test callback audit no body
    req = run_async(msteams_request_approval("test-user", "Title", "Desc"))
    aid = req["approval_id"]
    payload = {
        "approval_id": aid,
        "decision": "approved",
        "sender_user_id": "test-user",
        "reason": "SECRET_REASON_12345"
    }
    client.post(
        "/api/messages",
        headers={"X-MSTEAMS-MCP-SECRET": "test-secure-secret"},
        json=payload
    )

    with open(settings.msteams_audit_log_path, "r") as f:
        logs = f.read()
        assert secret_desc not in logs
        assert "SECRET_REASON_12345" not in logs

# --- INBOUND CALLBACK TESTS ---

def test_callback_missing_secret():
    """Missing inbound secret returns 401."""
    res = client.post("/api/messages", json={"approval_id": "app-1"})
    assert res.status_code == 401

def test_callback_wrong_secret():
    """Wrong inbound secret returns 401."""
    res = client.post(
        "/api/messages",
        headers={"X-MSTEAMS-MCP-SECRET": "wrong"},
        json={"approval_id": "app-1"}
    )
    assert res.status_code == 401

def test_callback_approved_success():
    """Approved decision succeeds for correct sender."""
    req = run_async(msteams_request_approval("test-user", "Title", "Desc"))
    aid = req["approval_id"]

    payload = {
        "approval_id": aid,
        "decision": "approved",
        "sender_user_id": "test-user",
        "reason": "Looks good"
    }
    res = client.post(
        "/api/messages",
        headers={"X-MSTEAMS-MCP-SECRET": "test-secure-secret"},
        json=payload
    )
    assert res.status_code == 200
    assert res.json() == {"status": "received", "approval_id": aid, "decision": "approved"}

    # Verify audit decision is ALLOWED (since status is 'received')
    import json
    with open(settings.msteams_audit_log_path, "r") as f:
        last_log = json.loads(f.readlines()[-1])
        assert last_log["decision"] == "ALLOWED"
        assert last_log["status"] == "received"

    # Verify state check via MCP tool
    status = run_async(msteams_get_approval(aid))
    assert status["state"] == "approved"

def test_callback_rejected_success():
    """Rejected decision succeeds for correct sender."""
    req = run_async(msteams_request_approval("test-user", "Title", "Desc"))
    aid = req["approval_id"]

    payload = {
        "approval_id": aid,
        "decision": "rejected",
        "sender_user_id": "test-user",
        "reason": "Denied"
    }
    res = client.post(
        "/api/messages",
        headers={"X-MSTEAMS-MCP-SECRET": "test-secure-secret"},
        json=payload
    )
    assert res.status_code == 200
    assert res.json() == {"status": "received", "approval_id": aid, "decision": "rejected"}

    # Verify audit decision is ALLOWED (since status is 'received')
    import json
    with open(settings.msteams_audit_log_path, "r") as f:
        last_log = json.loads(f.readlines()[-1])
        assert last_log["decision"] == "ALLOWED"
        assert last_log["status"] == "received"

    # Verify state check via MCP tool
    status = run_async(msteams_get_approval(aid))
    assert status["state"] == "rejected"

def test_callback_missing_sender():
    """Missing sender_user_id fails."""
    req = run_async(msteams_request_approval("test-user", "Title", "Desc"))
    aid = req["approval_id"]

    payload = {
        "approval_id": aid,
        "decision": "approved"
    }
    res = client.post(
        "/api/messages",
        headers={"X-MSTEAMS-MCP-SECRET": "test-secure-secret"},
        json=payload
    )
    assert res.status_code == 200
    assert res.json()["status"] == "error"

def test_callback_invalid_decision():
    """Invalid decision value fails."""
    req = run_async(msteams_request_approval("test-user", "Title", "Desc"))
    aid = req["approval_id"]

    payload = {
        "approval_id": aid,
        "decision": "maybe",
        "sender_user_id": "test-user"
    }
    res = client.post(
        "/api/messages",
        headers={"X-MSTEAMS-MCP-SECRET": "test-secure-secret"},
        json=payload
    )
    assert res.status_code == 200
    assert res.json()["status"] == "error"

def test_callback_unknown_approval():
    """Unknown approval_id fails."""
    payload = {
        "approval_id": "ghost-app",
        "decision": "approved",
        "sender_user_id": "test-user"
    }
    res = client.post(
        "/api/messages",
        headers={"X-MSTEAMS-MCP-SECRET": "test-secure-secret"},
        json=payload
    )
    assert res.status_code == 200
    assert res.json()["status"] == "error"

def test_callback_wrong_sender():
    """Wrong sender_user_id fails."""
    req = run_async(msteams_request_approval("test-user", "Title", "Desc"))
    aid = req["approval_id"]

    payload = {
        "approval_id": aid,
        "decision": "approved",
        "sender_user_id": "hacker"
    }
    res = client.post(
        "/api/messages",
        headers={"X-MSTEAMS-MCP-SECRET": "test-secure-secret"},
        json=payload
    )
    assert res.status_code == 200
    assert res.json()["status"] == "error"

def test_callback_duplicate_decision():
    """Duplicate decision fails."""
    req = run_async(msteams_request_approval("test-user", "Title", "Desc"))
    aid = req["approval_id"]

    # First decision
    payload = {
        "approval_id": aid,
        "decision": "approved",
        "sender_user_id": "test-user"
    }
    client.post(
        "/api/messages",
        headers={"X-MSTEAMS-MCP-SECRET": "test-secure-secret"},
        json=payload
    )

    # Second decision (duplicate)
    res = client.post(
        "/api/messages",
        headers={"X-MSTEAMS-MCP-SECRET": "test-secure-secret"},
        json=payload
    )
    assert res.status_code == 200
    assert res.json()["status"] == "error"

def test_callback_expired_approval():
    """Expired approval fails and is audited."""
    req = run_async(msteams_request_approval("test-user", "Title", "Desc"))
    aid = req["approval_id"]

    # Force expire the approval in store
    from agentic_msteams_mcp.approvals.store import store as app_store
    import datetime
    app_store._approvals[aid].expires_at = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(seconds=1)

    payload = {
        "approval_id": aid,
        "decision": "approved",
        "sender_user_id": "test-user"
    }
    res = client.post(
        "/api/messages",
        headers={"X-MSTEAMS-MCP-SECRET": "test-secure-secret"},
        json=payload
    )
    assert res.status_code == 200
    assert res.json()["status"] == "error"

    # Verify state persisted as expired
    state_res = run_async(msteams_get_approval(aid))
    assert state_res["state"] == "expired"

    # Verify audit entry exists and decision is DENIED (since status is 'error')
    import json
    with open(settings.msteams_audit_log_path, "r") as f:
        last_log = json.loads(f.readlines()[-1])
        assert "approval_callback" in last_log["event"]
        assert aid in last_log["target_id"]
        assert last_log["decision"] == "DENIED"
        assert last_log["status"] == "error"
