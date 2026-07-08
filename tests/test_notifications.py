import pytest
import asyncio
from fastapi.testclient import TestClient

from agentic_msteams_mcp.mcp_server import msteams_send_notification, msteams_ask_user, msteams_get_user_reply, mcp_server
from agentic_msteams_mcp.notifications.models import TargetType, Severity
from agentic_msteams_mcp.config import settings
from agentic_msteams_mcp.asks.store import store
from agentic_msteams_mcp.teams_app import teams_app

client = TestClient(teams_app)

def run_async(coro):
    return asyncio.run(coro)

@pytest.fixture(autouse=True)
def setup_config(tmp_path):
    settings.msteams_allowed_user_ids = ["test-user"]
    settings.msteams_allowed_channel_ids = ["test-chan"]
    settings.msteams_notification_dry_run = True
    settings.msteams_audit_log_path = str(tmp_path / "notifications_audit.log")
    settings.msteams_inbound_shared_secret = "test-secure-secret"

@pytest.fixture(autouse=True)
def clear_store():
    store._asks = {}

def test_mcp_inventory():
    tools = mcp_server._tool_manager.list_tools()
    names = [t.name for t in tools]
    expected_names = {
        "msteams_health_check",
        "msteams_send_notification",
        "msteams_ask_user",
        "msteams_get_user_reply",
        "msteams_request_approval",
        "msteams_get_approval",
    }
    assert set(names) == expected_names
    assert len(names) == 6

def test_notification_allowed():
    res = run_async(msteams_send_notification("user", "test-user", "Hi", "Msg", "info"))
    assert res["status"] == "success"
    assert "audit_id" in res

def test_notification_denied():
    res = run_async(msteams_send_notification("user", "hacker", "Hi", "Msg", "info"))
    assert res["status"] == "denied"
    assert "audit_id" in res

def test_ask_allowed():
    res = run_async(msteams_ask_user("test-user", "What is your name?"))
    assert res["status"] == "success"
    assert "request_id" in res
    assert "audit_id" in res

def test_ask_denied():
    res = run_async(msteams_ask_user("hacker", "What is your name?"))
    assert res["status"] == "denied"
    assert "audit_id" in res

def test_ask_validation():
    # Empty question
    res = run_async(msteams_ask_user("test-user", "  "))
    assert res["status"] == "error"
    assert "audit_id" in res
    
    # Oversized question
    res = run_async(msteams_ask_user("test-user", "A" * 2001))
    assert res["status"] == "error"

def test_get_reply_pending():
    ask_res = run_async(msteams_ask_user("test-user", "Hello?"))
    rid = ask_res["request_id"]
    reply_res = run_async(msteams_get_user_reply(rid, "test-user", "msteams_ask_user", "unknown"))
    assert reply_res["state"] == "pending"

def test_get_reply_answered():
    ask_res = run_async(msteams_ask_user("test-user", "Hello?"))
    rid = ask_res["request_id"]
    # Simulate external reply inject via store
    from agentic_msteams_mcp.asks.service import service as ask_svc
    asyncio.run(ask_svc.set_reply(rid, "I am a human", "test-user", "msteams_ask_user", "unknown"))
    
    reply_res = run_async(msteams_get_user_reply(rid, "test-user", "msteams_ask_user", "unknown"))
    assert reply_res["state"] == "answered"
    assert reply_res["reply"] == "I am a human"

def test_get_reply_unknown():
    # Use a valid-length ID to bypass basic validation and reach the store lookup
    res = run_async(msteams_get_user_reply("a" * 32, "test-user", "msteams_ask_user", "unknown"))
    assert res["state"] == "not_found"

def test_ask_expired():
    # Use an already allowed user to ensure we get a request_id
    # Min valid expires_in_seconds is 60
    ask_res = run_async(msteams_ask_user("test-user", "Hello?", expires_in_seconds=60))
    assert ask_res["status"] == "success"
    rid = ask_res["request_id"]
    
    # Force expiration in store
    from agentic_msteams_mcp.asks.store import store as s
    user_ask = s._asks[rid]
    import datetime
    user_ask.expires_at = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(seconds=1)
    
    reply_res = run_async(msteams_get_user_reply(rid, "test-user", "msteams_ask_user", "unknown"))
    assert reply_res["state"] == "not_found"

def test_audit_no_bodies():
    # Valid ask should not log the question in audit (based on generate_stable_fingerprint)
    ask_res = run_async(msteams_ask_user("test-user", "Secret Question?"))
    rid = ask_res["request_id"]
    
    import os
    with open(settings.msteams_audit_log_path, "r") as f:
        logs = f.read()
        assert "Secret Question?" not in logs

def test_teams_app_reply_success():
    # 1. Create an ask
    ask_res = run_async(msteams_ask_user("test-user", "Hello?"))
    rid = ask_res["request_id"]
    
    # 2. Send valid reply payload to teams_app with secret
    payload = {
        "reply_to": rid,
        "text": "I am here!",
        "target_user_id": "test-user",
        "tool_name": "msteams_ask_user",
        "requester_agent_id": "unknown"
    }
    res = client.post(
        "/api/messages", 
        headers={"X-MSTEAMS-MCP-SECRET": settings.msteams_inbound_shared_secret}, 
        json=payload
    )
    assert res.status_code == 200
    assert res.json() == {"status": "received", "request_id": rid}
    
    # 3. Verify state in store
    reply_res = run_async(msteams_get_user_reply(rid, "test-user", "msteams_ask_user", "unknown"))
    assert reply_res["state"] == "answered"
    assert reply_res["reply"] == "I am here!"

def test_teams_app_reply_missing_params():
    # Test missing target_user_id
    ask_res = run_async(msteams_ask_user("test-user", "Hello?"))
    rid = ask_res["request_id"]
    
    payloads = [
        {"reply_to": rid, "text": "hi", "tool_name": "t", "requester_agent_id": "a"}, # missing target
        {"reply_to": rid, "text": "hi", "target_user_id": "u", "requester_agent_id": "a"}, # missing tool
        {"reply_to": rid, "text": "hi", "target_user_id": "u", "tool_name": "t"}, # missing agent
    ]
    
    for p in payloads:
        res = client.post(
            "/api/messages", 
            headers={"X-MSTEAMS-MCP-SECRET": settings.msteams_inbound_shared_secret}, 
            json=p
        )
        assert res.status_code == 200
        assert res.json()["status"] == "error"
        assert "Missing security parameters" in res.json()["reason"]

def test_teams_app_reply_wrong_auth():
    # Test wrong binding parameters
    ask_res = run_async(msteams_ask_user("test-user", "Hello?"))
    rid = ask_res["request_id"]
    
    payload = {
        "reply_to": rid,
        "text": "hi",
        "target_user_id": "wrong-user",
        "tool_name": "msteams_ask_user",
        "requester_agent_id": "unknown"
    }
    res = client.post(
        "/api/messages", 
        headers={"X-MSTEAMS-MCP-SECRET": settings.msteams_inbound_shared_secret}, 
        json=payload
    )
    assert res.status_code == 200
    assert res.json()["status"] == "error"
    assert "Invalid request_id or authorization failure" in res.json()["reason"]
