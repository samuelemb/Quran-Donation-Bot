from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parents[3]
load_dotenv(BASE_DIR / ".env")


class Settings(BaseSettings):
    bot_token: str = Field(alias="BOT_TOKEN")
    database_url: str = Field(alias="DATABASE_URL")
    channel_link: str = Field(alias="CHANNEL_LINK")
    support_contact: str = Field(alias="SUPPORT_CONTACT")
    app_env: str = Field(default="development", alias="APP_ENV")
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    admin_api_key: str = Field(default="change-me", alias="ADMIN_API_KEY")
    enable_scheduler: bool = Field(default=False, alias="ENABLE_SCHEDULER")
    admin_email: str = Field(default="admin@qurandonation.org", alias="ADMIN_EMAIL")
    admin_password: str = Field(default="change-this-admin-password", alias="ADMIN_PASSWORD")
    admin_full_name: str = Field(default="Admin User", alias="ADMIN_FULL_NAME")
    admin_session_secret: str = Field(default="change-this-session-secret", alias="ADMIN_SESSION_SECRET")

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
