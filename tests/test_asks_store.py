import pytest
import os
import json
from pathlib import Path
from datetime import datetime, timezone, timedelta
from agentic_msteams_mcp.asks.models import UserAsk, AskState
from agentic_msteams_mcp.asks.store import AskStore
from agentic_msteams_mcp.config import settings

@pytest.fixture
def temp_state_file(tmp_path):
    return str(tmp_path / "state.json")

@pytest.fixture
def reset_settings(temp_state_file):
    # Save original values
    orig_durable = settings.msteams_use_durable_state
    orig_path = settings.msteams_state_store_path
    
    # Set test values
    settings.msteams_use_durable_state = False
    settings.msteams_state_store_path = temp_state_file
    
    yield
    
    # Restore
    settings.msteams_use_durable_state = orig_durable
    settings.msteams_state_store_path = orig_path

def create_mock_ask(rid="req-123"):
    return UserAsk(
        request_id=rid,
        target_user_id="test-user",
        question="What is 1+1?",
        created_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        state=AskState.PENDING,
        tool_name="test_tool",
        requester_agent_id="test_agent"
    )

def test_durable_disabled_remains_in_memory(reset_settings, temp_state_file):
    settings.msteams_use_durable_state = False
    store = AskStore()
    ask = create_mock_ask()
    
    import asyncio
    asyncio.run(store.save(ask))
    
    assert ask.request_id in store._asks
    assert not Path(temp_state_file).exists()

def test_durable_enabled_saves_to_json(reset_settings, temp_state_file):
    settings.msteams_use_durable_state = True
    store = AskStore()
    ask = create_mock_ask()
    
    import asyncio
    asyncio.run(store.save(ask))
    
    path = Path(temp_state_file)
    assert path.exists()
    with open(path, "r") as f:
        data = json.load(f)
    assert "asks" in data
    assert ask.request_id in data["asks"]

def test_durable_enabled_loads_into_new_instance(reset_settings, temp_state_file):
    settings.msteams_use_durable_state = True
    store1 = AskStore()
    ask = create_mock_ask()
    
    import asyncio
    asyncio.run(store1.save(ask))
    
    # Create new store instance to simulate restart
    store2 = AskStore()
    loaded_ask = asyncio.run(store2.get(ask.request_id))
    
    assert loaded_ask is not None
    assert loaded_ask.request_id == ask.request_id
    assert loaded_ask.question == ask.question

def test_durable_state_survives_updates(reset_settings, temp_state_file):
    settings.msteams_use_durable_state = True
    store1 = AskStore()
    ask = create_mock_ask()
    import asyncio
    asyncio.run(store1.save(ask))
    
    # Update state and reply
    asyncio.run(store1.update_state(ask.request_id, "answered", "2"))
    
    store2 = AskStore()
    loaded_ask = asyncio.run(store2.get(ask.request_id))
    assert loaded_ask.state == "answered"
    assert loaded_ask.reply_text == "2"

def test_preserves_unrelated_top_level_keys(reset_settings, temp_state_file):
    settings.msteams_use_durable_state = True
    path = Path(temp_state_file)
    
    # Pre-populate with some unrelated key
    initial_data = {"approvals": {"app-1": "some-val"}, "version": 1}
    path.write_text(json.dumps(initial_data))
    
    store = AskStore()
    ask = create_mock_ask()
    import asyncio
    asyncio.run(store.save(ask))
    
    with open(path, "r") as f:
        data = json.load(f)
    assert "asks" in data
    assert "approvals" in data
    assert data["version"] == 1

def test_corrupt_json_fails_safely(reset_settings, temp_state_file):
    settings.msteams_use_durable_state = True
    path = Path(temp_state_file)
    path.write_text("NOT JSON")
    
    # Should not crash during init
    store = AskStore()
    assert store._asks == {}

def test_existing_ask_logic_still_works(reset_settings):
    # Ensure that in-memory behavior for basic ops hasn't changed
    settings.msteams_use_durable_state = False
    store = AskStore()
    ask = create_mock_ask()
    import asyncio
    asyncio.run(store.save(ask))
    assert asyncio.run(store.get(ask.request_id)) == ask
