# Security

This document outlines the security model and considerations for agentic-msteams-mcp.

## Overview

The agentic-msteams-mcp server implements a secure gateway architecture that maintains separation between Microsoft Teams bot functionality and MCP agent capabilities. 

## Configuration Security

### Environment Variables
- All configuration is loaded from environment variables only
- No secrets are stored in the repository
- `.env.example` provides a template for configuration
- Production instances must set all required environment variables

### Required Configuration
The following environment variables are mandatory for production use:
- `TEAMS_APP_ID`: Microsoft Teams application identifier
- `TEAMS_APP_PASSWORD`: Microsoft Teams application password

The server will fail closed if these are not provided.

## Attack Surface Reduction

### Minimal Tool Inventory
- Only essential tools are implemented in v0.1.0
- No broad Microsoft Graph read/write capabilities
- No arbitrary command execution
- Limited to communication and health check capabilities

### Binding Security
- By default, the server binds to localhost only
- Explicit configuration required for external access  
- Network access restricted to configured hosts/ports

### No Persistent Storage
- No database or persistent storage of messages
- All processing is ephemeral
- No credential caching or persistent tokens

## Authorization Model

The current implementation:
1. Does not implement approval workflows 
2. Does not include complex authorization checks
3. Assumes appropriate access control at the Teams bot level

Future versions will expand upon these security measures with:
- Approval workflow implementations
- Enhanced role-based access controls
- Token management capabilities  

## Network Security

### Default Configuration
- Binds to localhost only by default (127.0.0.1)
- Ports configurable through environment variables  
- No automatic exposure of endpoints

### HTTPS Support
- No built-in HTTPS support in v0.1.0
- HTTPS should be handled at a reverse proxy level in production deployments

## Threat Model Considerations

### Internal Threats
The server does not process sensitive information beyond basic bot metadata, so threat impact is limited.

### External Threats  
- The main attack surface is the HTTP interfaces
- Protection relies on proper configuration and network segmentation
- No authentication required at the MCP level in v0.1.0 (to be expanded)

### Future Security Enhancements

Future development will include:
- Authentication/authorization headers for MCP endpoints
- Token-based authentication for Teams bot communication  
- Encrypted message handling capabilities
- More granular permissions models

## Compliance Considerations

This implementation currently provides basic security controls suitable for:
- Development and testing environments  
- Controlled internal deployments where appropriate access controls are enforced
