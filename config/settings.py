import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # Database
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", 5432))
    DB_USER: str = os.getenv("DB_USER", "postgres")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "postgres")
    DB_NAME: str = os.getenv("DB_NAME", "postgres")
    DB_SCHEMA: str = os.getenv("DB_SCHEMA", "public")
    ALLOW_MANIPULATION: bool = bool(os.getenv("ALLOW_MANIPULATION", "True"))

    # OpenAI
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "your_api_key_here")

    # Default LLM settings
    LOGIC_MODEL: str = os.getenv("LLM_MODEL", "gpt-4o-mini")
    GENERATION_MODEL: str = os.getenv("GENERATION_MODEL", "gpt-4o-mini")
    LOGIC_MODEL_TEMPERATURE: float = float(
        os.getenv("LOGIC_MODEL_TEMPERATURE", "1")
    )
    GENERATION_MODEL_TEMPERATURE: float = float(
        os.getenv("GENERATION_MODEL_TEMPERATURE", "0.5")
    )

    # Application settings
    MAX_HISTORY_ITEMS: int = int(os.getenv("MAX_HISTORY_ITEMS", "3"))

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # Security
    ENABLE_SQL_VALIDATION: bool = os.getenv(
        "ENABLE_SQL_VALIDATION", "True"
    ).lower() in ("true", "1", "t")
    SQL_QUERY_TIMEOUT: int = int(
        os.getenv("SQL_QUERY_TIMEOUT", "30")
    )  # Seconds


settings = Settings()
