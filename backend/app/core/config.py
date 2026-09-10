from pydantic import ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str
    JWT_SECRET: str
    JWT_EXPIRATION_HOURS: int = 24
    # Encrypts/decrypts admin_api_keys/org_api_credentials (AD-10, Story 6.5).
    # Deliberately a separate secret from JWT_SECRET -- a leaked session-
    # signing secret must not also decrypt stored API credentials.
    ADMIN_KEY_ENCRYPTION_SECRET: str
    ALLOWED_ORIGINS: str = "http://localhost:5173"
    SESSION_COOKIE_NAME: str = "access_token"
    COOKIE_SECURE: bool = True
    YOUTUBE_API_KEY: str | None = None

    @property
    def allowed_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]


def load_settings(**overrides) -> Settings:
    try:
        return Settings(**overrides)
    except ValidationError as exc:
        raise SystemExit(
            "ERROR: Missing or invalid configuration.\n"
            f"{exc}\n\n"
            "Copy backend/.env.example to backend/.env and fill in the required values "
            "(DATABASE_URL, JWT_SECRET), then retry."
        ) from exc


settings = load_settings()
