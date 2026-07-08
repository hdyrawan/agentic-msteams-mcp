# Security

This document outlines the security model and considerations for agentic-msteams-mcp.

## Overview

The agentic-msteams-mcp server implements a secure gateway architecture that maintains strict isolation between AI agents and the Microsoft Teams environment.

## Core Security Principles

### 1. Closed-World Toolset
To prevent "prompt injection" or agent hallucinations from causing unauthorized actions, the server exposes only six high-level tools:
- `msteams_health_check`
- `msteams_send_notification`
- `msteams_ask_user`
- `msteams_get_user_reply`
- `msteams_request_approval`
- `msteams_get_approval`

No arbitrary Graph API or Teams read/write tools are exposed.

### 2. Fail-Closed Allowlist Policy
The server employs a strict allowlist for all outbound communication. 
- **Enforcement**: Before any attempt to send a notification or ask a question, the target ID is checked against `MSTEAMS_ALLOWED_USER_IDS` and `MSTEAMS_ALLOWED_CHANNEL_IDS`.
- **Failure Mode**: If an ID is not explicitly allowlisted, the request is rejected with a `denied` status. An empty allowlist results in all requests being denied.

### 3. Privacy-Preserving Audit Logging
Every interaction attempt is recorded in an append-only audit log (`MSTEAMS_AUDIT_LOG_PATH`).
- **No Secrets**: Log entries never contain message bodies, question text, reply content, or authentication secrets.
- **Stable Identity**: Uses deterministic SHA-256 fingerprints of request metadata (target, severity, etc.) to allow auditors to track requests without seeing the sensitive payload.

### 4. Dry-Run Default
The server defaults to `MSTEAMS_NOTIFICATION_DRY_RUN=True`. This ensures that fresh deployments do not accidentally trigger notifications until explicitly configured for production delivery.

## Threat Model Analysis

| Threat | Mitigation |
| --- | --- |
| **Unauthorized Target** | Fail-closed allowlist blocks delivery to unknown users. |
| **Sensitive Data Leak in Logs** | Body-stripping fingerprinting ensures payload privacy in audit logs. |
| **Agent Hallucination (Tool Use)** | Closed toolset prevents agents from attempting arbitrary Graph API calls. |
| **Unauthenticated Webhook Injection** | Inbound callback authentication using a shared secret (X-MSTEAMS-MCP-SECRET) ensures that only authorized endpoints can trigger reply processing. This is enforced in a fail-closed manner. |

## Constraints
- No tenant user search tools are provided.
