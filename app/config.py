"""Configuration management using Pydantic Settings."""

import re
from functools import lru_cache
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Telegram Bot Configuration
    bot_token: str
    tg_webhook_secret: str

    # Webhook Registration
    webhook_url: str = ""
    webhook_max_connections: int = 40
    webhook_drop_pending: bool = True

    # Application Settings
    log_level: Literal["debug", "info", "warning", "error"] = "info"
    output_handler: Literal["stdout", "noop"] = "stdout"

    # Server Settings
    host: str = "0.0.0.0"
    port: int = 8000

    @field_validator("bot_token")
    @classmethod
    def validate_bot_token(cls, v: str) -> str:
        """Validate Telegram bot token format.
        
        Token format: 123456789:AAxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
        """
        pattern = r"^\d+:[A-Za-z0-9_-]+$"
        if not re.match(pattern, v):
            raise ValueError(
                "Invalid bot token format. Expected format: 123456789:AAxxxx..."
            )
        return v

    @field_validator("tg_webhook_secret")
    @classmethod
    def validate_webhook_secret(cls, v: str) -> str:
        """Validate webhook secret token.
        
        Must be 1-256 characters, only A-Z, a-z, 0-9, _ and - allowed.
        """
        if not v:
            raise ValueError("Webhook secret cannot be empty")
        if len(v) > 256:
            raise ValueError("Webhook secret must be 256 characters or less")
        pattern = r"^[A-Za-z0-9_-]+$"
        if not re.match(pattern, v):
            raise ValueError(
                "Webhook secret can only contain A-Z, a-z, 0-9, _ and -"
            )
        return v


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance.
    
    Settings are loaded once and cached for the lifetime of the application.
    """
    return Settings()

