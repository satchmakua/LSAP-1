"""Runtime configuration. Reads `.env` (see `.env.example`); secrets never hardcoded."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Claude models (see the claude-api skill for current IDs).
    anthropic_api_key: str = ""  # reads ANTHROPIC_API_KEY (same var the SDK uses)
    rater_model: str = "claude-opus-4-8"       # canonical rater / renderer
    second_rater_model: str = "claude-haiku-4-5"  # cheap convergence rater


settings = Settings()
