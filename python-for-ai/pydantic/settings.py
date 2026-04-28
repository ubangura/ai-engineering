from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env.example")

    # API Configuration
    api_key: SecretStr
    api_base_url: str = "https://api.example.com"
    request_timeout: int = Field(default=30, ge=1, le=300)

    # Database
    database_url: str
    max_connections: int = Field(default=10, ge=1, le=100)

    # Application
    debug: bool = False
    log_level: str = "INFO"


settings = Settings()

print(f"API URL: {settings.api_base_url}")
print(f"Timeout: {settings.request_timeout}s")
print(f"Debug mode: {settings.debug}")
