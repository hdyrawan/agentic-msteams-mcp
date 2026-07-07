# agentic-msteams-mcp

A self-hosted Microsoft Teams MCP server that serves as an agnostic human-in-the-loop gateway for AI agents.

## Overview

This project implements a dual-surface architecture to separate real-time bot communication from agent tool capabilities:
1. **Microsoft Teams Bot HTTP surface**: A secure webhook endpoint (`POST /api/messages`) for receiving and sending messages.
2. **MCP Server surface**: A standard MCP stdio server that provides tools for agents to interact with Teams.

v0.2.0 introduces a controlled notification foundation, allowing agents to send targeted notifications through an allowlist-protected gateway.

## Features

- **Secure Notification Gateway**: Send targets-limited notifications using an allowlist policy.
- **FastMCP Implementation**: Real MCP stdio protocol for tool execution.
- **Pydantic Validation**: Strict schema validation for all notification requests.
- **Audit Logging**: Append-only local audit logs of every delivery attempt.
- **Configurable and Hardened**: Fail-closed defaults, localhost binding, and environment-driven allowlists.

## Architecture

See `docs/architecture.md` for detailed architecture information.

## Security

See `docs/security.md` for security considerations.

## Configuration

Configuration is handled via environment variables. See `.env.example` for available options.

## Running Locally

### Prerequisites

- Python 3.11+
- Docker (optional, for building the image)

### Setup

```bash
# Clone or create the project directory
cd agentic-msteams-mcp

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .

# Copy example environment file
cp .env.example .env
```

### Run the Server(s)

v0.2.0 splits the surfaces clearly to avoid runtime conflicts.

#### 1. Start the MCP stdio server (for AI Agent use)
Run via the CLI entrypoint:
```bash
python -m agentic_msteams_mcp.main --mcp
```

#### 2. Start the Teams HTTP surface (//bot webhook)
Run via uvicorn:
```bash
uvicorn agentic_msteams_mcp.main:app --reload --host 0.0.0.0 --port 8000
```

### Run tests

```bash
pytest
```

### Build Docker image

```bash
docker build -t agentic-msteams-mcp:dev .
```

## Project Structure

```
agentic-msteams-mcp/
├── pyproject.toml
├── README.md
├── .env.example
├── Dockerfile
├── docker-compose.yml
├── src/agentic_msteams_mcp/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── mcp_server.py
│   ├── teams_app.py
│   ├── audit/
│   │   └── writer.py
│   │   ├── notifications/
│   │   └── policy/
│   │       └── tools/
│   │           └── health.py
│   └── tests/
│       ├── test_config.py
│       ├── test_health.py
│       └── test_notifications.py
└── docs/
    ├── architecture.md
    ├── security.md
    └── agent-config.md
```

## License

MIT License
