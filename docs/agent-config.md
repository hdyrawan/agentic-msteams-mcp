# Agent Configuration

This document describes how to configure and use agents with the agentic-msteams-mcp server.

## Overview

The MCP endpoint in agentic-msteams-mcp provides a structured interface for AI agents to communicate with Microsoft Teams through the server's gateway.

## Configuration Parameters

Agent configuration can be passed via environment variables or as part of the agent's own configuration mechanism. The following environment variables are available:

### Basic Server Configuration  
- `SERVER_HOST`: Hostname for the main HTTP endpoint (default: localhost)
- `SERVER_PORT`: Port number for the main HTTP endpoint (default: 8000)

### MCP Server Configuration
- `MCP_SERVER_HOST`: Hostname for MCP endpoint (default: localhost)  
- `MCP_SERVER_PORT`: Port number for MCP endpoint (default: 8001)

### Teams Configuration
- `TEAMS_APP_ID`: Microsoft Teams application identifier
- `TEAMS_APP_PASSWORD`: Microsoft Teams application password

## Agent Tool Usage

The MCP server provides the following tools that agents can invoke:

### `msteams_health_check`
Returns basic system health information for the Teams server.

Example usage:
```json
{
  "name": "msteams_health_check",
  "arguments": {}
}
```

## Future Configuration Extensions

In future versions, additional configuration options will be added to support:

1. Advanced authentication mechanisms
2. Agent-specific permission models  
3. Message routing and filtering rules
4. Integration with external security systems
5. Enhanced logging and monitoring controls

## Security Requirements

Agents connecting to this server must:
- Operate within appropriate network boundaries  
- Comply with the configured security policies
- Follow secure communication practices
- Not attempt to bypass access controls or configuration validation

## Integration Patterns

### Direct MCP Connection  
Agents can connect directly to the MCP endpoint at `/mcp/`.

### Teams Message Flow
Messages from Microsoft Teams pass through this server as a gateway:
1. Teams sends messages to `/api/messages` 
2. Server forwards relevant information to connected MCP agents
3. Agents can respond via the MCP protocol

## Testing Configuration

To test agent interactions with the server:

1. Start the server with `python -m agentic_msteams_mcp.main`
2. Call the health check endpoint:
   ```
   curl http://localhost:8000/mcp/health
   ```
3. Verify that agents can call MCP tools
