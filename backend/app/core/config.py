from functools import lru_cache
from pydantic_settings import BaseSettings

# Error codes
ERROR_SUCCESS = 0
ERROR_TOKEN_EXPIRED = 1001
ERROR_PERMISSION_DENIED = 1002
ERROR_INVALID_REQUEST = 1003
ERROR_NOT_FOUND = 1004
ERROR_INTERNAL = 2000


import os

class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    DATABASE_URL: str = f"sqlite:///{BASE_DIR}/data/br_app.db?check_same_thread=False&timeout=30"
    CHROMA_DB_PATH: str = f"{BASE_DIR}/data/chroma_db"

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
