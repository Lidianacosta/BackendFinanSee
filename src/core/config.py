"""Configuration management for FinanSee.

This module defines the application settings using Pydantic's BaseSettings.
"""

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings and environment variables."""

    database_url: str = Field(default="sqlite+aiosqlite:///db.sqlite")
    environment: str = Field(default="production")

    secret_key: str = Field(default="")
    algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=30)
    refresh_token_expire_minutes: int = Field(default=10080)  # 7 dias

    mail_username: str = Field(default="user@example.com")
    mail_password: str = Field(default="")
    mail_from: str = Field(default="no-reply@finansee.com")
    mail_port: int = Field(default=587)
    mail_server: str = Field(default="smtp.gmail.com")
    mail_from_name: str = Field(default="FinanSee")
    mail_starttls: bool = Field(default=True)
    mail_ssl_tls: bool = Field(default=False)
    use_credentials: bool = Field(default=True)

    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:3000"]
    )

    @model_validator(mode="after")
    def _validate_secrets(self) -> "Settings":
        """Fail fast in production if critical secrets are missing."""
        if self.environment == "production":
            missing = []
            if not self.secret_key:
                missing.append("SECRET_KEY")
            if not self.mail_password:
                missing.append("MAIL_PASSWORD")
            if missing:
                raise ValueError(
                    "Variáveis obrigatórias ausentes em produção: "
                    + ", ".join(missing)
                )
        return self

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
