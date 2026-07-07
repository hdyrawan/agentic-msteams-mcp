# Security

This document outlines the security model and considerations for agentic-msteams-mcp.

## Overview

The agentic-msteams-mcp server implements a secure gateway architecture that maintains separation between Microsoft Teams bot functionality and MCP agent capabilities. 

## Configuration Security

### Environment Variables
- All configuration is loaded from environment variables only via Pydantic Settings.
- No secrets are stored in the repository.
- `.env.example` provides a template for configuration.

### Mandatory Production Config
The server will fail closed if these are not provided in production:
- `TEAMS_APP_ID`: Microsoft Teams application identifier
- `TEAMS_APP_PASSWORD`: Microsoft Teams application password

## Attack Surface Reduction

### Minimal Tool Inventory (v0.2.0)
To prevent agent privilege escalation, the MCP server exposes exactly two tools:
1. `msteams_health_check`: Basic system diagnostic.
2. `msteams_send_notification`: Controlled notification delivery.

**Strict Constraints:**
- No broad Microsoft Graph read/write capabilities.
- No arbitrary command execution or VQL.
- No tool for listing users or channels.

### Notification Hardening
Notifications are protected by:
- **Allowlist Policy**: Only targets explicitly configured in `MSTEAMS_ALLOWED_USER_IDS` and `MSTEAMS_ALLOWED_CHANNEL_IDS` can receive notifications.
- **Strict Validation**: Pydantic models enforce maximum lengths for titles and messages to prevent buffer/rendering attacks.
- **Fail Closed**: Any target not found in the allowlist is rejected immediately.

### Binding Security
- By default, the server binds to `127.0.0.1` (localhost).
- Explicit configuration required for external access.

## Audit and Compliance

### Append-Only Logging
Every notification attempt—whether successful or denied—is recorded in a local audit log (`MSTEAMS_AUDIT_LOG_PATH`).
Audit records include:
- Timestamp, tool name, target metadata, decision (ALLOWED/DENIED), and reason.
- A stable SHA-256 fingerprint of the request for deduplication.

**Privacy Constraint:** The full message body is intentionally omitted from audit logs to prevent sensitive data leaks.

## Network Security

### Default Configuration
- Binds to localhost only by default.
- Ports are configurable through environment variables.

### HTTPS Support
- No built-in HTTPS support; it should be handled at a reverse proxy level (e.g., Nginx, Traefik) in production.

## Threat Model Considerations

### External Threats  
The primary attack surface is the HTTP interface and the MCP stdio channel. Protection relies on:
1. Proper configuration of allowlists.
2. Network segmentation.
3. Using a secure MCP client that only provides authorized tools to the agent.
