"""
Search Providers for IRIS

Abstract interface for web search with multiple backend implementations:
- BraveSearchProvider: Brave Search API (requires API key, rate limited)
- SearXNGProvider: Self-hosted SearXNG instance (unlimited, privacy-focused)

Provider selection priority:
1. SEARXNG_URL env var → SearXNG (preferred, no rate limits)
2. BRAVE_API_KEY env var → Brave Search API
3. Neither → returns configuration instructions
"""

import logging
import os
import threading
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import requests

logger = logging.getLogger(__name__)


# ==============================================================================
# Search Result Types
# ==============================================================================


@dataclass
class SearchResult:
    """A single search result."""
    title: str
    description: str
    url: str


@dataclass
class SearchResponse:
    """Response from a search query."""
    results: list[SearchResult]
    provider: str
    error: Optional[str] = None
    quota_alert: Optional[str] = None


# ==============================================================================
# Rate Limiter (shared with tools.py pattern)
# ==============================================================================


class RateLimiter:
    """Thread-safe rate limiter that queues requests."""

    def __init__(self, requests_per_second: float = 1.0):
        self.min_interval = 1.0 / requests_per_second
        self.last_request = 0.0
        self.lock = threading.Lock()

    def wait(self) -> float:
        """Wait if needed to respect rate limit. Returns wait time."""
        with self.lock:
            now = time.time()
            elapsed = now - self.last_request
            if elapsed < self.min_interval:
                wait_time = self.min_interval - elapsed
                time.sleep(wait_time)
                self.last_request = time.time()
                return wait_time
            self.last_request = now
            return 0.0


# ==============================================================================
# Abstract Base Provider
# ==============================================================================


class SearchProvider(ABC):
    """Abstract base class for search providers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name for logging."""
        pass

    @property
    @abstractmethod
    def is_configured(self) -> bool:
        """Whether this provider is properly configured."""
        pass

    @abstractmethod
    def search(self, query: str, count: int = 3) -> SearchResponse:
        """Execute a search query."""
        pass

    def configuration_instructions(self) -> str:
        """Instructions for configuring this provider."""
        return "Provider not configured."


# ==============================================================================
# Brave Search Provider
# ==============================================================================


# Quota tracking constants
MONTHLY_QUOTA = 2000
QUOTA_FILE = Path.home() / ".config" / "iris" / "brave_quota.json"


class BraveSearchProvider(SearchProvider):
    """Brave Search API provider with rate limiting and quota tracking."""

    def __init__(self, api_key: str):
        self._api_key = api_key
        self._rate_limiter = RateLimiter(requests_per_second=1.0)

    @property
    def name(self) -> str:
        return "Brave"

    @property
    def is_configured(self) -> bool:
        return bool(self._api_key)

    def configuration_instructions(self) -> str:
        return (
            "Brave Search is not configured. To enable it:\n"
            "1. Get a free API key at https://brave.com/search/api/\n"
            "2. Add to ~/.config/iris/secrets.env: BRAVE_API_KEY=your-key\n"
            "3. Restart IRIS"
        )

    def _load_quota(self) -> dict:
        """Load quota tracking from disk."""
        import json
        from datetime import datetime

        if not QUOTA_FILE.exists():
            return {"remaining": MONTHLY_QUOTA, "reset_date": ""}

        try:
            with open(QUOTA_FILE) as f:
                data = json.load(f)

            # Check if we need to reset (new month)
            reset_date = data.get("reset_date", "")
            if reset_date:
                reset = datetime.fromisoformat(reset_date)
                if datetime.now() >= reset:
                    return {"remaining": MONTHLY_QUOTA, "reset_date": ""}

            return data
        except Exception:
            return {"remaining": MONTHLY_QUOTA, "reset_date": ""}

    def _save_quota(self, remaining: int, reset_date: str) -> None:
        """Save quota tracking to disk."""
        import json

        QUOTA_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(QUOTA_FILE, "w") as f:
            json.dump({"remaining": remaining, "reset_date": reset_date}, f)

    def _update_quota_from_headers(self, headers: dict) -> Optional[str]:
        """Update quota from Brave API response headers."""
        from datetime import datetime

        remaining = headers.get("X-RateLimit-Remaining")
        reset_ts = headers.get("X-RateLimit-Reset")

        if remaining is not None:
            try:
                remaining_int = int(remaining)
                reset_date = ""
                if reset_ts:
                    reset_date = datetime.fromtimestamp(int(reset_ts)).isoformat()

                self._save_quota(remaining_int, reset_date)

                # Alert thresholds
                if remaining_int <= 100:
                    return f"\n\n[QUOTA ALERT: {remaining_int}/{MONTHLY_QUOTA} searches remaining this month]"
                elif remaining_int <= 500:
                    return f"\n\n[Quota: {remaining_int}/{MONTHLY_QUOTA} remaining]"
            except ValueError:
                pass
        return None

    def search(self, query: str, count: int = 3) -> SearchResponse:
        """Search using Brave Search API."""
        if not self.is_configured:
            return SearchResponse(
                results=[],
                provider=self.name,
                error=self.configuration_instructions()
            )

        # Check quota before making request
        quota = self._load_quota()
        if quota.get("remaining", MONTHLY_QUOTA) <= 0:
            reset_date = quota.get("reset_date", "unknown")
            return SearchResponse(
                results=[],
                provider=self.name,
                error=f"Web search quota exhausted (0/{MONTHLY_QUOTA}). Resets on {reset_date}."
            )

        count = max(1, min(5, count))

        try:
            wait_time = self._rate_limiter.wait()
            if wait_time > 0:
                logger.info(f"[Search] Brave rate limited, waited {wait_time:.2f}s")

            logger.info(f"[Search] Brave: '{query}' (count={count})")

            response = requests.get(
                "https://api.search.brave.com/res/v1/web/search",
                headers={
                    "Accept": "application/json",
                    "X-Subscription-Token": self._api_key,
                },
                params={
                    "q": query,
                    "count": count,
                    "safesearch": "moderate",
                },
                timeout=10,
            )

            quota_alert = self._update_quota_from_headers(response.headers)

            if response.status_code == 401:
                return SearchResponse(
                    results=[],
                    provider=self.name,
                    error="Brave API key is invalid. Please check your BRAVE_API_KEY."
                )
            elif response.status_code == 429:
                return SearchResponse(
                    results=[],
                    provider=self.name,
                    error="Brave rate limit reached. Please try again in a second."
                )
            elif response.status_code != 200:
                logger.error(f"[Search] Brave API error: {response.status_code}")
                return SearchResponse(
                    results=[],
                    provider=self.name,
                    error=f"Brave search failed (HTTP {response.status_code})"
                )

            data = response.json()
            web_results = data.get("web", {}).get("results", [])

            results = [
                SearchResult(
                    title=r.get("title", "No title"),
                    description=r.get("description", "No description"),
                    url=r.get("url", ""),
                )
                for r in web_results[:count]
            ]

            return SearchResponse(
                results=results,
                provider=self.name,
                quota_alert=quota_alert
            )

        except requests.Timeout:
            return SearchResponse(
                results=[],
                provider=self.name,
                error="Brave search timed out. Please try again."
            )
        except requests.RequestException as e:
            logger.error(f"[Search] Brave error: {e}")
            return SearchResponse(
                results=[],
                provider=self.name,
                error=f"Brave search failed: {str(e)}"
            )


# ==============================================================================
# SearXNG Provider
# ==============================================================================


class SearXNGProvider(SearchProvider):
    """Self-hosted SearXNG instance provider."""

    def __init__(self, base_url: str):
        self._base_url = base_url.rstrip("/")

    @property
    def name(self) -> str:
        return "SearXNG"

    @property
    def is_configured(self) -> bool:
        return bool(self._base_url)

    def configuration_instructions(self) -> str:
        return (
            "SearXNG is not configured. To enable it:\n"
            "1. Run SearXNG: docker run -p 8888:8080 searxng/searxng\n"
            "2. Add to ~/.config/iris/secrets.env: SEARXNG_URL=http://localhost:8888\n"
            "3. Restart IRIS\n\n"
            "Or use Brave Search API instead (see DEVELOPMENT.md)"
        )

    def search(self, query: str, count: int = 3) -> SearchResponse:
        """Search using SearXNG JSON API."""
        if not self.is_configured:
            return SearchResponse(
                results=[],
                provider=self.name,
                error=self.configuration_instructions()
            )

        count = max(1, min(10, count))

        try:
            logger.info(f"[Search] SearXNG: '{query}' (count={count})")

            response = requests.get(
                f"{self._base_url}/search",
                params={
                    "q": query,
                    "format": "json",
                    "categories": "general",
                },
                headers={
                    "Accept": "application/json",
                },
                timeout=15,  # SearXNG may be slower (aggregates multiple engines)
            )

            if response.status_code != 200:
                logger.error(f"[Search] SearXNG error: {response.status_code}")
                return SearchResponse(
                    results=[],
                    provider=self.name,
                    error=f"SearXNG search failed (HTTP {response.status_code})"
                )

            data = response.json()
            raw_results = data.get("results", [])

            results = [
                SearchResult(
                    title=r.get("title", "No title"),
                    description=r.get("content", r.get("description", "No description")),
                    url=r.get("url", ""),
                )
                for r in raw_results[:count]
            ]

            return SearchResponse(results=results, provider=self.name)

        except requests.Timeout:
            return SearchResponse(
                results=[],
                provider=self.name,
                error="SearXNG search timed out. Check if the server is running."
            )
        except requests.ConnectionError:
            return SearchResponse(
                results=[],
                provider=self.name,
                error=f"Cannot connect to SearXNG at {self._base_url}. Is it running?"
            )
        except requests.RequestException as e:
            logger.error(f"[Search] SearXNG error: {e}")
            return SearchResponse(
                results=[],
                provider=self.name,
                error=f"SearXNG search failed: {str(e)}"
            )


# ==============================================================================
# Provider Factory
# ==============================================================================


def _load_secrets() -> dict:
    """Load secrets from config file."""
    secrets_file = Path.home() / ".config" / "iris" / "secrets.env"
    secrets = {}
    if secrets_file.exists():
        with open(secrets_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    secrets[key.strip()] = value.strip()
    return secrets


def get_search_provider() -> SearchProvider:
    """
    Get the configured search provider.

    Priority:
    1. SEARXNG_URL → SearXNG (unlimited, self-hosted)
    2. BRAVE_API_KEY → Brave Search API (rate limited)
    3. None configured → returns provider with error instructions
    """
    secrets = _load_secrets()

    # Check for SearXNG first (preferred - no rate limits)
    searxng_url = secrets.get("SEARXNG_URL") or os.environ.get("SEARXNG_URL", "")
    if searxng_url:
        logger.info(f"[Search] Using SearXNG provider: {searxng_url}")
        return SearXNGProvider(searxng_url)

    # Fall back to Brave
    brave_key = secrets.get("BRAVE_API_KEY") or os.environ.get("BRAVE_API_KEY", "")
    if brave_key:
        logger.info("[Search] Using Brave Search provider")
        return BraveSearchProvider(brave_key)

    # No provider configured - return Brave with empty key (will show instructions)
    logger.warning("[Search] No search provider configured")
    return BraveSearchProvider("")


# Singleton provider instance
_provider: Optional[SearchProvider] = None


def get_provider() -> SearchProvider:
    """Get the singleton search provider instance."""
    global _provider
    if _provider is None:
        _provider = get_search_provider()
    return _provider


def web_search(query: str, count: int = 3) -> str:
    """
    Execute a web search using the configured provider.

    Returns formatted string for LLM consumption.
    """
    provider = get_provider()
    response = provider.search(query, count)

    if response.error:
        return response.error

    if not response.results:
        result = f"No results found for '{query}'"
        if response.quota_alert:
            result += response.quota_alert
        return result

    # Format results for LLM consumption
    formatted = []
    for i, r in enumerate(response.results, 1):
        formatted.append(f"{i}. {r.title}\n   {r.description}\n   URL: {r.url}")

    result = f"Search results for '{query}' (via {response.provider}):\n\n"
    result += "\n\n".join(formatted)

    if response.quota_alert:
        result += response.quota_alert

    return result
