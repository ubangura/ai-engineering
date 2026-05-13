from typing import Literal

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

APP_NAME = "Distill"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    anthropic_api_key: SecretStr
    deepgram_api_key: SecretStr
    database_url: str
    session_cookie_secret: SecretStr
    allowed_origins: str = ""
    environment: Literal["production", "development"] = "production"
    youtube_cookies_path: str | None = None
    yt_dlp_node_path: str = "node"

    @property
    def is_dev(self) -> bool:
        return self.environment == "development"

    @property
    def cors_origins(self) -> list[str]:
        if self.allowed_origins:
            return [origin.strip() for origin in self.allowed_origins.split(",")]
        return []


settings = Settings()
