"""Configuration module for Meross Dual Gateway."""


from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class MerossSettings(BaseSettings):
    """Configuration settings for Meross Cloud connection and Dual Gateway."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Meross Cloud Account Credentials
    email: str = Field(
        default="",
        validation_alias=AliasChoices("MEROSS_EMAIL", "email"),
        description="Meross Cloud account email address",
    )
    password: str = Field(
        default="",
        validation_alias=AliasChoices("MEROSS_PASSWORD", "password"),
        description="Meross Cloud account password",
    )
    api_base_url: str = Field(
        default="https://iotx-eu.meross.com",
        validation_alias=AliasChoices("MEROSS_API_BASE_URL", "api_base_url"),
        description="Regional Meross Cloud API base endpoint (default: Europe)",
    )

    # Server Gateway Network Settings
    host: str = Field(
        default="0.0.0.0",
        validation_alias=AliasChoices("MEROSS_GATEWAY_HOST", "host"),
        description="Bind host for the HTTP/REST/SSE Gateway server",
    )
    port: int = Field(
        default=8112,
        validation_alias=AliasChoices("MEROSS_GATEWAY_PORT", "port"),
        description="Bind port for the HTTP/REST/SSE Gateway server",
    )

    # Security Settings (Optional)
    api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("MEROSS_GATEWAY_API_KEY", "api_key"),
        description="Optional API Key required for mutative REST API calls (X-API-Key header)",
    )
