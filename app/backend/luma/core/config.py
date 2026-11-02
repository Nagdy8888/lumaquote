from functools import lru_cache
from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[4]


class Settings(BaseSettings):
    """Typed server configuration loaded from ignored environment files; secrets remain server-only."""

    model_config = SettingsConfigDict(env_file=(ROOT / ".env", ROOT / ".env.local"), extra="ignore")
    supabase_url: str = "http://127.0.0.1:55321"
    supabase_anon_key: SecretStr = SecretStr("")
    supabase_service_role_key: SecretStr = SecretStr("")
    database_url: SecretStr = SecretStr("")
    luma_api_database_url: SecretStr = SecretStr("")
    luma_worker_database_url: SecretStr = SecretStr("")
    openai_api_key: SecretStr = SecretStr("")
    openai_model: str = "gpt-6-luna"
    transcription_model: str = "gpt-transcribe"
    embedding_model: str = "text-embedding-3-small"
    langsmith_api_key: SecretStr = SecretStr("")
    langsmith_project: str = "quotation-assistant"
    langsmith_endpoint: str = "https://api.smith.langchain.com"
    langsmith_tracing: bool = False
    whatsapp_token: SecretStr = SecretStr("")
    whatsapp_app_secret: SecretStr = SecretStr("")
    whatsapp_verify_token: SecretStr = SecretStr("")
    whatsapp_phone_id: str = ""
    whatsapp_company_id: str = ""
    whatsapp_test_recipients: str = ""
    whatsapp_graph_version: str = "v26.0"
    google_sheet_id: str = ""
    google_callback_secret: SecretStr = SecretStr("")
    google_company_id: str = ""
    total_budget: float = 25
    daily_budget: float = 5
    reservation: float = 0.25
    enable_paid_ai: bool = False
    enable_live_whatsapp: bool = False


@lru_cache
def settings() -> Settings:
    """Return the cached validated configuration; clear the cache only after an intentional local setup change."""
    return Settings()
