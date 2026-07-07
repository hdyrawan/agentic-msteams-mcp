# Agent Configuration

This document describes how to configure and use agents with the agentic-msteams-mcp server.

## Overview

The MCP endpoint in agentic-msteams-mcp provides a structured interface for AI agents to communicate with Microsoft Teams through the server's gateway.

## Configuration Parameters

Agent configuration is handled via environment variables. The following parameters are relevant:

### Basic Server Configuration  
- `SERVER_HOST`: Hostname for the main HTTP endpoint (default: 127.0.0.1)
- `SERVER_PORT`: Port number for the main HTTP endpoint (default: 8000)

### Notification Control
- `MSTEAMS_NOTIFICATION_DRY_RUN`: Boolean flag. If true, notifications are simulated and not sent to Graph API. Default: `True`.
- `MSTEAMS_ALLOWED_USER_IDS`: Comma-separated list of allowed Microsoft Teams User IDs.
- `MSTEAMS_ALLOWED_CHANNEL_IDS`: Comma-separated list of allowed Microsoft Teams Channel IDs.
- `MSTEAMS_AUDIT_LOG_PATH`: Absolute path to the audit log file (default: `data/notifications_audit.log`).

### Teams Configuration
- `TEAMS_APP_ID`: Microsoft Teams application identifier
- `TEAMS_APP_PASSWORD`: Microsoft Teams application password

## Agent Tool Usage

The MCP server provides exactly two tools that agents can invoke:

### `msteams_health_check`
Returns basic system health information for the Teams server.

### `msteams_send_notification`
Sends a notification to an allowlisted target. 
**Constraint**: The agent must provide a valid `target_type`, `target_id`, `title`, `message`, and `severity`. If the `target_id` is not in the configured allowlist, the tool will return a `denied` status.

## Integration Patterns

### MCP Connection (Stdio)
Agents should connect to this server via stdio transport. 
Example CLI start: `python -m agentic_msteams_mcp.main --mcp`

### Teams Message Flow
Messages from Microsoft Teams pass through the HTTP surface:
1. Teams sends messages to `POST /api/messages`.
2. Server forwards relevant information to connected MCP agents (via separate orchestration).
3. Agents respond via the MCP protocol tools.
