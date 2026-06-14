"""Application configuration loaded from the environment."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Maximum number of records a single generation request may produce.
    max_records: int = 100_000

    # Number of rows returned by the preview step.
    preview_rows: int = 10

    # OpenAI configuration. When the key is absent, LLM-backed features
    # (ERP schema inference, contextual data fallback) are disabled.
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"

    @property
    def llm_enabled(self) -> bool:
        return bool(self.openai_api_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()
