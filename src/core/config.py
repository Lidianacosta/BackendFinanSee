from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = Field(default="sqlite+aiosqlite:///db.sqlite")
    environment: str = Field(default="production")

    secret_key: str = Field(
        default="09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
    )
    algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=30)

    # Email Settings
    mail_username: str = Field(default="user@example.com")
    mail_password: str = Field(default="password")
    mail_from: str = Field(default="no-reply@finansee.com")
    mail_port: int = Field(default=587)
    mail_server: str = Field(default="smtp.gmail.com")
    mail_from_name: str = Field(default="FinanSee")
    mail_starttls: bool = Field(default=True)
    mail_ssl_tls: bool = Field(default=False)
    use_credentials: bool = Field(default=True)

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
