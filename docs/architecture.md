# Architecture

This project implements a dual-surface architecture for Microsoft Teams integration with MCP (Model Communication Protocol) agents.

## Overview

The agentic-msteams-mcp server provides two distinct interfaces:
1. A Microsoft Teams bot HTTP endpoint
2. An MCP endpoint for AI agents

Both are served by the same FastAPI application to maintain simplicity while providing a secure gateway pattern that can be extended with additional features.

## Architecture Diagram

```plaintext
┌─────────────────┐    ┌──────────────────┐
│   Microsoft     │    │    AI Agents     │
│   Teams Bot     │    │   (MCP Clients)  │
└─────────┬───────┘    └──────────┬───────┘
          │                     │
          └─────────────────────┘
                       │
        ┌────────────────┴────────────────┐
        │      agentic-msteams-mcp        │
        │    Dual-Surface Server          │
        │  ┌─────────────────────────────┐ │
        │  │        Teams Endpoint       │ │
        │  │   (/api/messages)         │ │
        │  └─────────────────────────────┘ │
        │  ┌─────────────────────────────┐ │
        │  │        MCP Endpoint         │ │
        │  │    (/mcp/health, etc.)    │ │
        │  └─────────────────────────────┘ │
        └──────────────────────────────────┘
```

## Components

### Teams Endpoint (`/api/messages`)
- Handles incoming Microsoft Teams messages
- Serves as a gateway for bot interactions
- Processes messages and forwards them to the agent layer

### MCP Server (`/mcp/*`)
- Provides standard MCP endpoints for AI agents
- Health check tools for monitoring
- Future extension points for additional command tools

## Security Considerations

The implementation follows security best practices:

1. Configuration validation from environment variables
2. Binding to localhost by default unless explicitly configured  
3. Fail closed on missing required production configuration
4. Minimal tool inventory to reduce attack surface
5. No broad Microsoft Graph access in v0.1.0

## Future Development Plans

1. Implement actual Microsoft Teams SDK integration and Graph API delivery (Current versions utilize Dry-Run as the safe default).
2. Expand allowlist capabilities to support group-based permissions.
3. Integrate with enterprise identity providers for dynamic user discovery.
4. Optional Durable State: Add configuration flags (`msteams_use_durable_state`) to enable persisting pending asks and approvals across restarts. Default remains in-memory.

The current v0.5.0a implementation provides the full set of MCP tools for notifications, asks, and approvals, while maintaining a secure dry-run delivery model by default to prevent accidental production triggers.
