import pytest
import asyncio
from agentic_msteams_mcp.mcp_server import msteams_send_notification, msteams_ask_user, msteams_get_user_reply, mcp_server
from agentic_msteams_mcp.notifications.models import TargetType, Severity
from agentic_msteams_mcp.config import settings
from agentic_msteams_mcp.asks.store import store

def run_async(coro):
    return asyncio.run(coro)

@pytest.fixture(autouse=True)
def setup_config():
    settings.msteams_allowed_user_ids = ["test-user"]
    settings.msteams_allowed_channel_ids = ["test-chan"]
    settings.msteams_notification_dry_run = True

@pytest.fixture(autouse=True)
def clear_store():
    store._asks = {}

def test_mcp_inventory():
    tools = mcp_server._tool_manager.list_tools()
    names = [t.name for t in tools]
    assert len(names) == 4
    assert "msteams_health_check" in names
    assert "msteams_send_notification" in names
    assert "msteams_ask_user" in names
    assert "msteams_get_user_reply" in names

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
    reply_res = run_async(msteams_get_user_reply(rid))
    assert reply_res["state"] == "pending"

def test_get_reply_answered():
    ask_res = run_async(msteams_ask_user("test-user", "Hello?"))
    rid = ask_res["request_id"]
    # Simulate external reply inject via store
    from agentic_msteams_mcp.asks.service import service as ask_svc
    asyncio.run(ask_svc.set_reply(rid, "I am a human"))
    
    reply_res = run_async(msteams_get_user_reply(rid))
    assert reply_res["state"] == "answered"
    assert reply_res["reply"] == "I am a human"

def test_get_reply_unknown():
    res = run_async(msteams_get_user_reply("ghost-id"))
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
    
    reply_res = run_async(msteams_get_user_reply(rid))
    assert reply_res["state"] == "expired"

def test_audit_no_bodies():
    # Valid ask should not log the question in audit (based on generate_stable_fingerprint)
    ask_res = run_async(msteams_ask_user("test-user", "Secret Question?"))
    rid = ask_res["request_id"]
    
    import os
    with open(settings.msteams_audit_log_path, "r") as f:
        logs = f.read()
        assert "Secret Question?" not in logs
