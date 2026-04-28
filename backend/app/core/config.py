from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/br_app.db"
    CHROMA_DB_PATH: str = "./data/chroma_db"

    JWT_SECRET_KEY: str = "change-me"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 1440

    ANTHROPIC_API_KEY: str = ""

    HOST: str = "0.0.0.0"
    PORT: int = 8000

    model_config = {"env_file": ".env", "extra": "ignore"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
