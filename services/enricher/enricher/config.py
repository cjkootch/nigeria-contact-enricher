from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./data/ncec_enricher.db")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    search_provider: str = os.getenv("SEARCH_PROVIDER", "stub")
    duckduckgo_region: str = os.getenv("DUCKDUCKGO_REGION", "wt-wt")
    user_agent: str = os.getenv("USER_AGENT", "NCEC-Enricher/0.1 (+local)")
    request_timeout_seconds: int = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "20"))
    request_delay_seconds: float = float(os.getenv("REQUEST_DELAY_SECONDS", "1"))
    max_retries: int = int(os.getenv("MAX_RETRIES", "3"))
    enable_playwright: bool = os.getenv("ENABLE_PLAYWRIGHT", "false").lower() == "true"
    brave_api_key: str = os.getenv("BRAVE_API_KEY", "")


settings = Settings()

SCORING_WEIGHTS = {
    "title_exact": 20,
    "body_exact": 15,
    "fuzzy_name": 20,
    "domain_similarity": 15,
    "category_match": 10,
    "nigeria_signal": 10,
    "contact_about_exists": 5,
    "branding_consistency": 5,
}
