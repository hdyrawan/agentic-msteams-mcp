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

1. Implement actual Microsoft Teams SDK integration
2. Add approval workflow capabilities (v0.2.0)
3. Extend with Velo/MISP-specific logic (v0.3.0+)
4. Add broader Microsoft Graph support (v0.4.0+) 

The current v0.1.0 implementation focuses on proving the architecture and establishing a secure communication channel between human-in-the-loop agents and Microsoft Teams.
