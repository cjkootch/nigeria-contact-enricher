from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from .config import settings

logger = logging.getLogger(__name__)

EXCLUDED_DOMAINS = {
    "facebook.com",
    "linkedin.com",
    "instagram.com",
    "twitter.com",
    "x.com",
    "wikipedia.org",
    "youtube.com",
    "google.com",
    "bing.com",
}


@dataclass
class SearchResult:
    url: str
    title: str
    snippet: str


class SearchProvider:
    def search(self, query: str, limit: int = 5) -> list[SearchResult]:
        raise NotImplementedError


class StubSearchProvider(SearchProvider):
    def search(self, query: str, limit: int = 5) -> list[SearchResult]:
        return [SearchResult(url="https://example.com", title=f"Stub for {query}", snippet="")]


class DuckDuckGoSearchProvider(SearchProvider):
    base_url = "https://duckduckgo.com/html/"

    def search(self, query: str, limit: int = 5) -> list[SearchResult]:
        time.sleep(settings.request_delay_seconds)
        response = requests.get(
            self.base_url,
            params={"q": query, "kl": settings.duckduckgo_region},
            timeout=settings.request_timeout_seconds,
            headers={"User-Agent": settings.user_agent},
        )
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        results: list[SearchResult] = []
        for item in soup.select(".result"):
            link = item.select_one("a.result__a")
            snippet = item.select_one(".result__snippet")
            if not link:
                continue
            url = link.get("href", "")
            parsed = urlparse(url)
            domain = parsed.netloc.lower().replace("www.", "")
            if any(domain.endswith(x) for x in EXCLUDED_DOMAINS):
                continue
            results.append(
                SearchResult(url=url, title=link.get_text(strip=True), snippet=snippet.get_text(" ", strip=True) if snippet else "")
            )
            if len(results) >= limit:
                break
        return results


def get_search_provider() -> SearchProvider:
    if settings.search_provider == "duckduckgo":
        return DuckDuckGoSearchProvider()
    logger.warning("Using stub search provider")
    return StubSearchProvider()
