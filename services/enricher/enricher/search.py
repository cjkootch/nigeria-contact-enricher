from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from urllib.parse import parse_qs

from .config import settings

logger = logging.getLogger(__name__)

EXCLUDED_DOMAINS = {
    # Social / forums
    "facebook.com", "linkedin.com", "instagram.com", "twitter.com", "x.com",
    "reddit.com", "quora.com", "youtube.com", "tiktok.com", "pinterest.com",
    "medium.com", "tumblr.com",
    # Search engines / reference
    "google.com", "bing.com", "wikipedia.org", "wiktionary.org",
    "dictionary.com", "britannica.com",
    # Business registries / aggregators
    "crunchbase.com", "opencorporates.com", "bloomberg.com", "dnb.com",
    "companieshistory.com", "bizdirectory.com.ng", "company-information.service.gov.uk",
    "find-and-update.company-information.service.gov.uk",
    "nigeria24.me", "ng-check.com", "b2bhint.com", "mkt-icp.com", "icpcredit.com",
    "nigerianfinder.com", "nigeriayp.com", "finelib.com", "connectnigeria.com",
    "vconnect.com", "businesslist.com.ng", "businesscheck.co.nz",
    # Reviews / jobs / maps
    "trustpilot.com", "glassdoor.com", "indeed.com", "yellowpages.com",
    "yelp.com", "sulekha.com", "mapquest.com", "foursquare.com",
    # Misc noise observed in earlier runs
    "gitexnigeria.ng", "savycon.com",
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
        response = None
        for attempt in range(settings.max_retries):
            response = requests.get(
                self.base_url,
                params={"q": query, "kl": settings.duckduckgo_region},
                timeout=settings.request_timeout_seconds,
                headers={"User-Agent": settings.user_agent},
            )
            if response.status_code not in (429, 503):
                break
            backoff = settings.request_delay_seconds * (2 ** attempt) + attempt
            logger.warning("DDG %s for %r, sleeping %.1fs (attempt %d/%d)", response.status_code, query, backoff, attempt + 1, settings.max_retries)
            time.sleep(backoff)
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
            if parsed.netloc.endswith("duckduckgo.com") and parsed.path == "/l/":
                uddg = parse_qs(parsed.query).get("uddg", [""])[0]
                if uddg:
                    url = uddg
                    parsed = urlparse(url)
            if not parsed.scheme:
                url = "https:" + url if url.startswith("//") else "https://" + url.lstrip("/")
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
    if settings.search_provider == "brave":
        return BraveSearchProvider()
    if settings.search_provider == "duckduckgo":
        return DuckDuckGoSearchProvider()
    logger.warning("Using stub search provider")
    return StubSearchProvider()


class BraveSearchProvider(SearchProvider):
    base_url = "https://api.search.brave.com/res/v1/web/search"

    def __init__(self) -> None:
        if not settings.brave_api_key:
            raise RuntimeError("BRAVE_API_KEY not set")

    def search(self, query: str, limit: int = 5) -> list[SearchResult]:
        time.sleep(settings.request_delay_seconds)
        response = None
        for attempt in range(settings.max_retries):
            response = requests.get(
                self.base_url,
                params={"q": query, "count": min(limit, 20)},
                timeout=settings.request_timeout_seconds,
                headers={
                    "X-Subscription-Token": settings.brave_api_key,
                    "Accept": "application/json",
                    "User-Agent": settings.user_agent,
                },
            )
            if response.status_code not in (429, 503):
                break
            backoff = settings.request_delay_seconds * (2 ** attempt) + attempt
            logger.warning("Brave %s for %r, sleeping %.1fs (attempt %d/%d)", response.status_code, query, backoff, attempt + 1, settings.max_retries)
            time.sleep(backoff)
        response.raise_for_status()
        payload = response.json()
        results: list[SearchResult] = []
        for item in (payload.get("web") or {}).get("results", []):
            url = item.get("url") or ""
            domain = urlparse(url).netloc.lower().replace("www.", "")
            if any(domain.endswith(x) for x in EXCLUDED_DOMAINS):
                continue
            results.append(SearchResult(url=url, title=item.get("title", ""), snippet=item.get("description", "")))
            if len(results) >= limit:
                break
        return results
