from functools import lru_cache
import logging
import os
from pydantic import BaseModel, Field


def setup_logging():
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )


class LLMSettings(BaseModel):
    temperature: float = 0.0
    max_tokens: int | None = None
    max_retries: int = 3


class OpenAISettings(LLMSettings):
    api_key: str = Field(default_factory=lambda: os.getenv("OPENAI_API_KEY"))
    model: str = "gpt-4o-mini"


class GigaChatSettings(LLMSettings):
    api_key: str = Field(default_factory=lambda: os.getenv("GIGACHAT_API_KEY"))
    model: str = "GigaChat-Max"


class DatabaseSettings(BaseModel):
    host: str = os.getenv("DB_HOST", "localhost")
    port: int = int(os.getenv("DB_PORT", 5432))
    user: str = os.getenv("DB_USER", "postgres")
    password: str = os.getenv("DB_PASSWORD", "postgres")
    name: str = os.getenv("DB_NAME", "postgres")
    schema: str = os.getenv("DB_SCHEMA", "public")


class Settings(BaseModel):
    # Database
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    openai: OpenAISettings = Field(default_factory=OpenAISettings)
    gigachat: GigaChatSettings = Field(default_factory=GigaChatSettings)
    allow_manipulation: bool = bool(os.getenv("ALLOW_MANIPULATION", "True"))
    default_llm_provider: str = os.getenv("DEFAULT_LLM_PROVIDER", "openai")


@lru_cache
def get_settings():
    settings = Settings()
    setup_logging()
    return settings
