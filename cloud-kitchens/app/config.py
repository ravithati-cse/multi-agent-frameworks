from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_ENV: str = "development"
    SECRET_KEY: str = "change-me"
    DEBUG: bool = True

    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/cloud_kitchens"
    REDIS_URL: str = "redis://localhost:6379/0"

    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""

    DELIVERY_PROVIDER: str = "internal"

    ANTHROPIC_API_KEY: str = ""
    OPENAI_API_KEY: str = ""


settings = Settings()
