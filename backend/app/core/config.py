from pathlib import Path

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[3]
BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=(ROOT_DIR / ".env", BACKEND_DIR / ".env", ".env"), extra="ignore")

    database_url: str = "sqlite+aiosqlite:///./prototree_local.db"
    jwt_secret: str = "change-me-in-prod"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7  # default 7 days
    remember_token_expire_minutes: int = 60 * 24 * 30  # remember-me 30 days
    sliding_renew_threshold_minutes: int = 60 * 24 * 3  # renew if remaining < 3 days

    ai_provider: str = "custom"
    ai_api_key: str = Field(default="", validation_alias=AliasChoices("AI_API_KEY", "OPENAI_API_KEY", "ai_api_key", "openai_api_key"))
    ai_base_url: str = Field(default="", validation_alias=AliasChoices("AI_BASE_URL", "OPENAI_BASE_URL", "ai_base_url", "openai_base_url"))
    ai_model: str = Field(default="", validation_alias=AliasChoices("AI_MODEL", "OPENAI_MODEL", "ai_model", "openai_model"))

    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    storage_dir: str = str(ROOT_DIR / "storage")

    # SMTP for password reset
    smtp_host: str = "smtp.qq.com"
    smtp_port: int = 465
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from_name: str = "Lu Lab"
    reset_link_base: str = "https://lulab.top/reset-password"


settings = Settings()
