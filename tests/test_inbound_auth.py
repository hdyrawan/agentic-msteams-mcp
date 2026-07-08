import pytest
from fastapi.testclient import TestClient
from agentic_msteams_mcp.teams_app import teams_app
from agentic_msteams_mcp.config import settings
from agentic_msteams_mcp.asks.service import service as ask_service
import asyncio

client = TestClient(teams_app)

@pytest.fixture(autouse=True)
def setup_auth():
    # Default secure state for tests
    settings.msteams_require_inbound_auth = True
    settings.msteams_inbound_shared_secret = "test-secure-secret"

def test_auth_missing_secret():
    """Missing X-MSTEAMS-MCP-SECRET header returns 401."""
    res = client.post("/api/messages", json={"id": "msg1"})
    assert res.status_code == 401
    assert res.json()["detail"] == "Missing inbound secret"

def test_auth_wrong_secret():
    """Incorrect X-MSTEAMS-MCP-SECRET header returns 401."""
    res = client.post(
        "/api/messages", 
        headers={"X-MSTEAMS-MCP-SECRET": "wrong-secret"}, 
        json={"id": "msg1"}
    )
    assert res.status_code == 401
    assert res.json()["detail"] == "Invalid inbound secret"

def test_auth_empty_configured_secret():
    """Empty configured shared secret fails closed when auth is required."""
    settings.msteams_inbound_shared_secret = ""
    res = client.post(
        "/api/messages", 
        headers={"X-MSTEAMS-MCP-SECRET": "any-secret"}, 
        json={"id": "msg1"}
    )
    assert res.status_code == 401
    assert res.json()["detail"] == "Inbound auth not configured"

def test_auth_correct_secret():
    """Correct inbound secret allows valid request flow."""
    res = client.post(
        "/api/messages", 
        headers={"X-MSTEAMS-MCP-SECRET": "test-secure-secret"}, 
        json={"id": "msg1"}
    )
    # Should not be 401; for a non-reply msg, it returns 200 received
    assert res.status_code == 200

def test_auth_disabled():
    """Auth disabled allows valid reply flow without secret."""
    settings.msteams_require_inbound_auth = False
    res = client.post("/api/messages", json={"id": "msg1"})
    assert res.status_code == 200

def test_failed_auth_does_not_set_reply():
    """Failed auth does not process or store replies."""
    # Setup an ask
    rid = "test-req-id"
    # Using asyncio.run to call the async service directly if needed, 
    # but here we can just check that set_reply was NOT called 
    # by checking a state before/after or using a mock if available.
    # Since we have store, let's use it.
    from agentic_msteams_mcp.asks.store import store
    store._asks = {} # Ensure empty

    payload = {
        "reply_to": rid,
        "text": "Hacked!",
        "target_user_id": "test-user",
        "tool_name": "t",
        "requester_agent_id": "a"
    }
    
    res = client.post("/api/messages", json=payload) # No secret provided
    assert res.status_code == 401
    assert rid not in store._asks
