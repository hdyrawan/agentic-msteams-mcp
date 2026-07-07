# agentic-msteams-mcp

A self-hosted Microsoft Teams MCP server that serves as an agnostic human-in-the-loop gateway for AI agents.

## Overview

This project implements a dual-surface architecture to allow AI agents to interact with humans via Microsoft Teams without requiring the agent to have direct Graph API access or complex bot logic.

### v0.3.0 Feature: Ask/Reply Workflow
v0.3.0 introduces the ability for agents to pose structured questions to users and track responses asynchronously.

- **`msteams_ask_user`**: Poses a question to an allowlisted user. Returns a `request_id`.
- **`msteams_get_user_reply`**: Checks if a user has replied to a specific request.

## Core Architecture

### 1. The MCP Surface (Stdio)
The primary interface for AI agents. It exposes a strictly limited toolset:
- `msteams_health_check`: Verifies server connectivity.
- `msteams_send_notification`: Sends one-way alerts to allowlisted users/channels.
- `msteams_ask_user`: Requests information from an allowlisted user (v0.3.0+).
- `msteams_get_user_reply`: Checks the state of a requested reply (v0.3.0+).

### 2. The Teams Surface (HTTP)
A lightweight FastAPI app that acts as the webhook receiver for Microsoft Teams. It is designed to be hosted behind a proxy/gateway.

## Security Model (Secure-by-Design)

### Closed-World Toolset
The server explicitly denies any arbitrary Graph API operations. All interactions are gated through specific, high-level tools.

### Fail-Closed Allowlist
Notifications and Asks are only delivered to IDs defined in the `MSTEAMS_ALLOWED_USER_IDS` or `MSTEAMS_ALLOWED_CHANNEL_IDS` environment variables. If an ID is not listed, the request is rejected immediately.

### Audit Logging
Every attempt to notify or ask a user is logged to a local audit file (`MSTEAMS_AUDIT_LOG_PATH`). 
- **Privacy**: Log entries contain metadata and fingerprints but NEVER include the actual message or question body.
- **Stability**: Uses SHA-256 deterministic fingerprinting for audit evidence.

### Dry-Run Mode
By default, `MSTEAMS_NOTIFICATION_DRY_RUN=True`. In this mode, the server validates all requests and logs them to audit but does not actually call the Microsoft Graph API.

## Installation & Configuration

### Environment Variables
| Variable | Default | Description |
| --- | --- | --- |
| `SERVER_HOST` | `127.0.0.1` | Bind address for the HTTP surface. |
| `SERVER_PORT` | `8000` | Port for the HTTP surface. |
| `MSTEAMS_ALLOWED_USER_IDS` | `""` | Comma-separated list of allowlisted User IDs (Required). |
| `MSTEAMS_ALLOWED_CHANNEL_IDS` | `""` | Comma-separated list of allowlisted Channel IDs. |
| `MSTEAMS_NOTIFICATION_DRY_RUN` | `True` | If true, no real Graph API calls are made. |
| `MSTEAMS_AUDIT_LOG_PATH` | `data/audit.log` | Path to the append-only audit log file. |

### Running the Server
The server provides two distinct modes:

**1. MCP Stdio Mode (for AI Agents)**
```bash
python -m agentic_msteams_mcp.main --mcp
```

**2. HTTP Surface Mode (for Teams Webhooks)**
```bash
python -m agentic_msteams_mcp.main --http
```

## Deployment

The server is provided as a Docker image for consistent runtime environments.
```bash
docker build -t agentic-msteams-mcp .
docker run -p 8000:8000 -e MSTEAMS_ALLOWED_USER_IDS="user1,user2" agentic-msteams-mcp --http
```
