"""Runtime configuration. Reads `backend/.env` (see `.env.example`) or the process
environment; secrets are never hardcoded. `ANTHROPIC_API_KEY` maps to `anthropic_api_key`.
"""

from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Absolute path so `.env` loads no matter which directory the server is launched from.
_ENV_FILE = Path(__file__).resolve().parents[2] / ".env"  # -> backend/.env


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(_ENV_FILE), extra="ignore")

    # Claude models (see the claude-api skill for current IDs).
    anthropic_api_key: str = ""  # reads ANTHROPIC_API_KEY (env or backend/.env)
    rater_model: str = "claude-opus-4-8"       # canonical rater / renderer
    second_rater_model: str = "claude-haiku-4-5"  # cheap convergence rater


settings = Settings()
