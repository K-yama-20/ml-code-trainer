from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(ROOT / ".env"), extra="ignore")
    app_env: str = "development"
    database_url: str = "sqlite:///./trainer.db"
    web_origin: str = "http://127.0.0.1:5173"
    supabase_url: str = ""
    supabase_audience: str = "authenticated"
    execution_provider: str = "disabled"
    modal_token_id: str = ""
    modal_token_secret: str = ""

    @property
    def modal_ready(self):
        return self.execution_provider=='modal' and bool(self.modal_token_id and self.modal_token_secret)


settings = Settings()
if settings.app_env == "production" and (
    not settings.supabase_url or not settings.database_url.startswith("postgresql")
):
    raise RuntimeError("Production requires Supabase Auth and PostgreSQL")
