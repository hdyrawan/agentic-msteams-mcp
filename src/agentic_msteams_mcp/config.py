"""Configuration management for agentic-msteams-mcp."""

from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Microsoft Teams Configuration (optional for testing/dev)
    teams_app_id: str = ""
    teams_app_password: str = ""
    
    # Server Configuration
    server_host: str = "localhost"
    server_port: int = 8000
    
    # MCP Configuration  
    mcp_server_host: str = "localhost"
    mcp_server_port: int = 8001
    
    # Logging Configuration
    log_level: str = "INFO"
    
    # Development Flags
    debug: bool = False
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# Global settings instance
settings = Settings()