from functools import lru_cache

from pydantic import PostgresDsn, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.ai.anthropic_backend import Effort


class Settings(BaseSettings):
    """Configuration lue depuis l'environnement (voir .env.example à la racine)."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: str = "development"
    database_url: PostgresDsn = PostgresDsn(
        "postgresql+psycopg://tamasheq:tamasheq@localhost:5432/tamasheq"
    )
    cors_origins: list[str] = ["http://localhost:3000"]

    # Assistant : désactivé tant qu'aucune clé n'est fournie.
    anthropic_api_key: SecretStr | None = None
    chat_model: str = "claude-opus-5-5"
    chat_effort: Effort = "medium"
    chat_requests_per_minute: int = 10


@lru_cache
def get_settings() -> Settings:
    return Settings()
