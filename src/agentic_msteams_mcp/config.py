from pydantic import Field
from pydantic_settings import BaseSettings
from typing import Optional, List

class Settings(BaseSettings):
    # Inbound Callback Authentication
    msteams_inbound_shared_secret: str = ""
    msteams_require_inbound_auth: bool = True
    
    # Microsoft Teams Configuration (optional for testing/dev)
    teams_app_id: str = ""
    teams_app_password: str = ""
    
    # Notification Control
    msteams_notification_dry_run: bool = True
    msteams_allowed_user_ids: List[str] = Field(default_factory=list)
    msteams_allowed_channel_ids: List[str] = Field(default_factory=list)
    msteams_audit_log_path: str = "data/notifications_audit.log"

    # Durable State Configuration (v0.5.0a)
    msteams_use_durable_state: bool = False
    msteams_state_store_path: str = "data/state.json"
    
    # Server Configuration
    server_host: str = "127.0.0.1"
    server_port: int = 8000
    
    # MCP Configuration  
    mcp_server_host: str = "127.0.0.1"
    mcp_server_port: int = 8001
    
    # Logging Configuration
    log_level: str = "INFO"
    
    # Development Flags
    debug: bool = False
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore"
    }

# Global settings instance
settings = Settings()
