import logging
from dataclasses import dataclass
from typing import Any

from django.conf import settings

from mapping.services.enrichment.cache import EnrichmentCache
from mapping.services.enrichment.http import HTTPConfig, ResilientHTTPClient

logger = logging.getLogger(__name__)


@dataclass
class WikimediaPageCandidate:
    language: str
    title: str
    pageid: int
    snippet: str
    score: float
    reason: str


class WikimediaClient:
    """Cliente HTTP isolado para Wikimedia/Wikipedia com headers obrigatórios."""

    SEARCH_ENDPOINT = "/w/api.php"

    def __init__(self):
        timeout = float(getattr(settings, "WIKIMEDIA_TIMEOUT_SECONDS", 8))
        retries = int(getattr(settings, "WIKIMEDIA_HTTP_RETRIES", 2))
        self.cache = EnrichmentCache(ttl_seconds=int(getattr(settings, "ENRICH_CACHE_TTL_WIKIMEDIA", 3600 * 24)))
        self.clients = {
            "pt": ResilientHTTPClient(HTTPConfig(base_url="https://pt.wikipedia.org", timeout_seconds=timeout, retries=retries)),
            "en": ResilientHTTPClient(HTTPConfig(base_url="https://en.wikipedia.org", timeout_seconds=timeout, retries=retries)),
        }
        self.default_headers = {
            "User-Agent": settings.WIKIMEDIA_USER_AGENT,
            "Api-User-Agent": settings.WIKIMEDIA_API_USER_AGENT,
        }

    def _request_json(self, language: str, params: dict[str, Any], *, cache_namespace: str, cache_payload: dict[str, Any]) -> tuple[dict[str, Any] | list, str | None]:
        cached = self.cache.get(cache_namespace, cache_payload)
        if cached is not None:
            return cached.get("payload", {}), cached.get("error")

        client = self.clients[language]
        if hasattr(client, "session"):
            client.session.headers.update(self.default_headers)

        payload, error = client.get_json(self.SEARCH_ENDPOINT, params=params)
        self.cache.set(cache_namespace, cache_payload, {"payload": payload, "error": error})
        return payload, error

    def search_page_candidates(self, *, query: str, language: str = "pt", limit: int = 5) -> tuple[list[dict[str, Any]], str | None]:
        params = {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "srlimit": limit,
            "format": "json",
            "utf8": 1,
        }
        payload, error = self._request_json(
            language,
            params,
            cache_namespace="wikimedia-search",
            cache_payload={"language": language, "query": query, "limit": limit},
        )
        results = payload.get("query", {}).get("search", []) if isinstance(payload, dict) else []
        return results if isinstance(results, list) else [], error

    def fetch_page_extract(self, *, language: str, title: str) -> tuple[dict[str, Any], str | None]:
        params = {
            "action": "query",
            "prop": "extracts|pageprops",
            "explaintext": 1,
            "exintro": 0,
            "titles": title,
            "redirects": 1,
            "format": "json",
            "utf8": 1,
        }
        payload, error = self._request_json(
            language,
            params,
            cache_namespace="wikimedia-extract",
            cache_payload={"language": language, "title": title},
        )
        pages = payload.get("query", {}).get("pages", {}) if isinstance(payload, dict) else {}
        if not isinstance(pages, dict):
            return {}, error or "not_found"
        for _, page in pages.items():
            if isinstance(page, dict) and not page.get("missing"):
                return page, error
        return {}, error or "not_found"

    def classify_error(self, error: str | None) -> str:
        if not error:
            return "none"
        text = str(error).lower()
        if "429" in text:
            return "rate_limited"
        if "timed out" in text or "timeout" in text:
            return "timeout"
        if "circuit_open" in text:
            return "circuit_open"
        if "name or service not known" in text or "connection" in text:
            return "network_error"
        return "external_error"
