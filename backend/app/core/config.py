"""Application settings and environment configuration."""

from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment or .env file."""

    TURSO_DATABASE_URL: Optional[str] = None
    TURSO_AUTH_TOKEN: Optional[str] = None
    ENVIRONMENT: str = "development"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    def __repr__(self) -> str:
        token_display = "***" if self.TURSO_AUTH_TOKEN else None
        return (
            f"Settings(TURSO_DATABASE_URL={self.TURSO_DATABASE_URL!r}, "
            f"TURSO_AUTH_TOKEN={token_display!r}, "
            f"ENVIRONMENT={self.ENVIRONMENT!r})"
        )

    def __str__(self) -> str:
        return self.__repr__()


settings = Settings()
