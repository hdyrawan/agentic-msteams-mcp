# Use Python 3.12 slim image as base for compatibility
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy pyproject.toml and src first for proper editable install
COPY pyproject.toml ./
COPY src/ ./src/

# Install the package in editable mode
RUN pip install --no-cache-dir -e .

# Expose ports for both servers
EXPOSE 8000 8001

# Default command to run the application
CMD ["uvicorn", "agentic_msteams_mcp.main:app", "--host", "0.0.0.0", "--port", "8000"]