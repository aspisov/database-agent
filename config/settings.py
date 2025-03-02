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

    # OpenAI
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "your_api_key_here")

    # Default LLM settings
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4o-mini")
    LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.7"))

    # Agent-specific models (using the default if not specified)
    ROUTER_MODEL: str = os.getenv("ROUTER_MODEL", LLM_MODEL)
    TEXT2SQL_MODEL: str = os.getenv("TEXT2SQL_MODEL", LLM_MODEL)
    VISUALIZATION_MODEL: str = os.getenv("VISUALIZATION_MODEL", LLM_MODEL)
    CHAT_MODEL: str = os.getenv("CHAT_MODEL", LLM_MODEL)

    # Agent-specific temperatures
    ROUTER_TEMPERATURE: float = (
        0.2  # Lower temperature for more consistent classifications
    )
    TEXT2SQL_TEMPERATURE: float = 0.3  # Moderate temperature for SQL generation
    VISUALIZATION_TEMPERATURE: float = (
        0.5  # Medium temperature for visualization code
    )
    CHAT_TEMPERATURE: float = (
        0.7  # Higher temperature for more creative chat responses
    )

    # Application settings
    MAX_TOKENS: int = int(os.getenv("MAX_TOKENS", "2000"))
    MAX_HISTORY_ITEMS: int = int(os.getenv("MAX_HISTORY_ITEMS", "10"))

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
