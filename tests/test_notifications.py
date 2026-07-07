import pytest
import asyncio
from agentic_msteams_mcp.mcp_server import msteams_send_notification, mcp_server
from agentic_msteams_mcp.notifications.models import TargetType, Severity
from agentic_msteams_mcp.config import settings

def run_async(coro):
    return asyncio.run(coro)

def test_notification_success():
    '''Test valid dry-run notification succeeds for allowlisted target.'''
    # Inject config for test
    settings.msteams_allowed_user_ids = ["user-123"]
    result = run_async(msteams_send_notification(
        target_type="user",
        target_id="user-123",
        title="Alert",
        message="System healthy",
        severity="info"
    ))
    assert result["status"] == "success"
    assert result["delivered"] is True
    assert result["dry_run"] is True
    assert "audit_id" in result

def test_notification_unknown_target_type():
    '''Test unknown target type is rejected.'''
    result = run_async(msteams_send_notification(
        target_type="invalid",
        target_id="user-123",
        title="Alert",
        message="System healthy",
        severity="info"
    ))
    assert result["status"] == "error"
    assert "Validation failed" in result["reason"]

def test_notification_non_allowlisted_target():
    '''Test non-allowlisted target is rejected.'''
    # Empty allowlist to ensure restriction
    settings.msteams_allowed_user_ids = []
    result = run_async(msteams_send_notification(
        target_type="user",
        target_id="evil-hacker-id",
        title="Alert",
        message="System healthy",
        severity="info"
    ))
    assert result["status"] == "denied"
    assert "not in allowlist" in result["reason"]

def test_notification_empty_fields():
    '''Test empty title/message is rejected.'''
    result = run_async(msteams_send_notification(
        target_type="user",
        target_id="user-123",
        title="",
        message="System healthy",
        severity="info"
    ))
    assert result["status"] == "error"

def test_notification_unsupported_severity():
    '''Test unsupported severity is rejected.'''
    result = run_async(msteams_send_notification(
        target_type="user",
        target_id="user-123",
        title="Alert",
        message="System healthy",
        severity="ultra-critical"
    ))
    assert result["status"] == "error"

def test_notification_length_limit():
    '''Test message length limit is enforced.'''
    result = run_async(msteams_send_notification(
        target_type="user",
        target_id="user-123",
        title="Alert",
        message="a" * 4001,
        severity="info"
    ))
    assert result["status"] == "error"

def test_mcp_inventory():
    '''Verify MCP tool inventory contains exactly the required tools.'''
    tools = mcp_server._tool_manager.list_tools()
    tool_names = [t.name for t in tools]
    assert len(tool_names) == 2
    assert "msteams_health_check" in tool_names
    assert "msteams_send_notification" in tool_names

def test_audit_log_creation():
    '''Verify audit record is written for allowed and denied attempts.'''
    import os
    # Use the configurable path from settings
    audit_path = settings.msteams_audit_log_path
    if os.path.exists(audit_path):
        os.remove(audit_path)
    
    # Allowed attempt
    settings.msteams_allowed_user_ids = ["test-user"]
    run_async(msteams_send_notification(
        target_type="user", target_id="test-user", title="T1", message="M1", severity="info"
    ))
    # Denied attempt
    run_async(msteams_send_notification(
        target_type="user", target_id="unknown", title="T2", message="M2", severity="info"
    ))
    
    with open(audit_path, "r") as f:
        lines = f.readlines()
    
    assert len(lines) == 2
    assert "ALLOWED" in lines[0]
    assert "DENIED" in lines[1]
