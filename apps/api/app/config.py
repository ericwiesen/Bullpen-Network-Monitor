import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/monitoring")
    redis_url: str = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    api_host: str = "0.0.0.0"
    api_port: int = int(os.environ.get("PORT", "8000"))

    class Config:
        env_file = ".env"


settings = Settings()
