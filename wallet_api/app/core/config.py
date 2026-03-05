from pydantic_settings import BaseSettings
from pydantic import ConfigDict


class Settings(BaseSettings):
    "Application settings loaded from environment variables or .env file"
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/wallet_db"

    # App
    APP_NAME: str = "Wallet API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    model_config = ConfigDict(env_file=".env", case_sensitive=True)


settings = Settings()
