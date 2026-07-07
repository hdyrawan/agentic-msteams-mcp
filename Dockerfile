# Use Python 3.12 slim image as base for compatibility
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy pyproject.toml and src first for proper editable install
COPY pyproject.toml ./
COPY src/ ./src/

# Install the package in editable mode
RUN pip install --no-cache-dir -e .

# Expose ports for Teams HTTP surface
EXPOSE 8000

# Default command runs the HTTP surface. 
# To run MCP stdio, override CMD or use a different entrypoint in compose.
CMD ["python", "-m", "agentic_msteams_mcp.main", "--http"]
