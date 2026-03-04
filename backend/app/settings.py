from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Faces CRM API"
    server_port: int = 8001  # Default port, can override with PORT env var

    # Example: postgresql+asyncpg://postgres:password@localhost:5432/faces
    database_url: str = "postgresql+asyncpg://postgres:Saad654321@localhost:5432/faces"

    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8001",
        "http://127.0.0.1:8001",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()

