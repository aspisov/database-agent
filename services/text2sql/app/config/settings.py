import logging
import os
from functools import lru_cache

from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()


def setup_logging():
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )


class LLMSettings(BaseModel):
    temperature: float = 1
    top_p: float = 0.6
    max_tokens: int | None = None
    timeout: int = 600


class OpenAISettings(LLMSettings):
    api_key: str | None = Field(default_factory=lambda: os.getenv("OPENAI_API_KEY"))
    model: str = "gpt-4o-mini"


class DatabaseSettings(BaseModel):
    host: str = os.getenv("DB_HOST", "host.docker.internal")
    port: int = int(os.getenv("DB_PORT", 5432))
    user: str = os.getenv("DB_USER", "postgres")
    password: str = os.getenv("DB_PASSWORD", "postgres")
    db_name: str = os.getenv("DB_NAME", "postgres")
    schema_name: str = os.getenv("DB_SCHEMA", "public")


class Settings(BaseModel):
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    openai: OpenAISettings = Field(default_factory=OpenAISettings)


@lru_cache
def get_settings():
    return Settings()
