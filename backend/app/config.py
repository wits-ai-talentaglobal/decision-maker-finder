from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# .env lives at the project root (one level above backend/), not inside backend/,
# so it's found regardless of the working directory the server is launched from.
_PROJECT_ROOT_ENV_FILE = Path(__file__).resolve().parent.parent.parent / ".env"


class Settings(BaseSettings):
    """App configuration, loaded from environment variables / .env.

    No secret ever has a hardcoded default here — an unset key means the
    corresponding integration is disabled, not silently misconfigured.
    """

    model_config = SettingsConfigDict(env_file=_PROJECT_ROOT_ENV_FILE, extra="ignore")

    # Stage 1: company identity + LinkedIn resolution (OpenRouter / Perplexity Sonar)
    openrouter_api_key: str | None = None
    openrouter_model: str = "perplexity/sonar"

    # Stage 2: employee scrape (Apify)
    apify_api_token: str | None = None
    apify_employees_actor_id: str = "harvestapi/linkedin-company-employees"

    # Stages 3-4: decision-maker extraction + validation (Claude API, direct)
    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-sonnet-5"

    # Stage 5: contact enrichment (Apollo.io)
    apollo_api_key: str | None = None

    # Stage 6: email fallback (Hunter.io) — may be unset; stage degrades gracefully
    hunter_api_key: str | None = None

    # Database
    database_url: str = "sqlite+aiosqlite:///./decision_maker_finder.db"

    # Backend server
    backend_cors_origins: str = "http://localhost:5173"
    job_concurrency_limit: int = 5
    batch_confirmation_threshold: int = 10

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.backend_cors_origins.split(",") if origin.strip()]


settings = Settings()
