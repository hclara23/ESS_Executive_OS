from typing import Optional

from pydantic_settings import BaseSettings


def _normalize_database_url(database_url: str) -> str:
    if database_url.startswith("postgresql+asyncpg://"):
        return database_url
    if database_url.startswith("postgresql://"):
        return database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    if database_url.startswith("postgres://"):
        return database_url.replace("postgres://", "postgresql+asyncpg://", 1)
    return database_url

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://ess_user:ess_secure_password_change_me@localhost:5432/ess_ags"
    REDIS_URL: str = "redis://localhost:6379/0"
    
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    LLM_PROVIDER: str = "openai"
    
    WP_URL: str = "https://your-wordpress-site.com"
    WP_USERNAME: str = ""
    WP_PASSWORD: str = ""
    WP_JWT_SECRET: str = ""
    
    GA4_PROPERTY_ID: Optional[str] = None
    GA4_CREDENTIALS: Optional[str] = None
    
    JWT_SECRET_KEY: str = "ess_local_dev_secret_change_in_production"
    JWT_ALGORITHM: str = "HS256"
    
    class Config:
        env_file = ".env"

    @property
    def async_database_url(self) -> str:
        return _normalize_database_url(self.DATABASE_URL)

settings = Settings()
