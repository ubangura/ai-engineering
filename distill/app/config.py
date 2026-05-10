from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    anthropic_api_key: SecretStr
    deepgram_api_key: SecretStr
    database_url: str
    session_cookie_secret: SecretStr
    allowed_origins: str
    environment: str

    @property
    def is_dev(self) -> bool:
        return self.environment == "development"

    @property
    def cors_origins(self) -> list[str]:
        if not self.allowed_origins:
            return []
        return [origin.strip() for origin in self.allowed_origins.split(",")]


settings = Settings()
