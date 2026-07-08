# Agent Configuration

This document describes how to configure and use agents with the agentic-msteams-mcp server.

## Overview

The MCP endpoint in agentic-msteams-mcp provides a structured interface for AI agents to communicate with humans via Microsoft Teams while maintaining strict security boundaries.

## Available Tools (v0.4.0)

### 1. `msteams_health_check`
Verifies that the server is running and its basic dependencies are available.
- **Response**: {status: "ok", ...}

### 2. `msteams_send_notification`
Sends a one-way alert to an allowlisted user or channel.
- **Inputs**: `target_type`, `target_id`, `title`, `message`, `severity`.
- **Security**: Fails closed if target is not in the allowlist.

### 3. `msteams_ask_user`
Poses a structured question to an allowlisted user and tracks it asynchronously.
- **Inputs**: `target_user_id`, `question`, `expires_in_seconds`.
- **Behavior**: Returns a `request_id`. The agent must later poll for the reply.

### 4. `msteams_get_user_reply`
Checks the current state of a specific ask request.
- **Inputs**: `request_id`.
- **Possible States**:
    - `pending`: No reply yet.
    - `answered`: User has responded. (Includes binary response text).
    - `expired`: Requesttimed out based on `expires_in_seconds`.
    - `not_found`: Invalid or unknown request ID.

### 5. `msteams_request_approval`
Initiates a formal approval/rejection request to an allowlisted user.
- **Inputs**: `target_user_id`, `action_description`, `expires_in_seconds`.
- **Behavior**: Returns a `request_id` for the approval token.

### 6. `msteams_get_approval`
Checks whether a specific approval request has been decided.
- **Inputs**: `request_id`.
- **Possible States**:
    - `pending`: Decision not yet made.
    - `approved`: User approved the action.
    - `rejected`: User rejected the action.
    - `expired`: Request timed out.
    - `not_found`: Invalid or unknown request ID.

## Configuration for Agents

Agents should be instructed to:
1. **Check Health**: Start by calling `msteams_health_check` to ensure the gateway is available.
2. **Use Notifications for Alerts**: Use `msteams_send_notification` for one-way status updates.
3. **Ask then Poll**: When a human response is needed:
    - Call `msteams_ask_user`.
    - Record the `request_id`.
    - Periodically call `msteams_get_user_reply(request_id)` until the state becomes `answered` or `expired`.
4. **Request Approvals**: For sensitive actions requiring a binary decision:
    - Call `msteams_request_approval`.
    - Periodically poll `msteams_get_approval(request_id)` for a final status (`approved` or `rejected`).

## Security Constraints for Agents
Agents cannot:
- Search for users in the tenant.
- Read arbitrary Teams messages or channel history.
- Modify user settings or permissions.
- Bypass the allowlist by guessing IDs.
