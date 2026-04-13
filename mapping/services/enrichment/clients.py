import logging
from dataclasses import dataclass
from typing import Any

import requests
from django.core.cache import cache

from mapping.utils.cache_keys import build_safe_cache_key

logger = logging.getLogger(__name__)


@dataclass
class APIClientConfig:
    base_url: str
    timeout: float = 6.0
    cache_ttl: int = 3600
    default_params: dict[str, Any] | None = None


class CachedHTTPClient:
    def __init__(self, config: APIClientConfig):
        self.config = config
        self.session = requests.Session()

    def get_json(self, path: str = "", *, params: dict[str, Any] | None = None, cache_key: str | None = None) -> dict[str, Any]:
        key = cache_key or build_safe_cache_key("http-client", self.config.base_url, path, params or {})
        cached = cache.get(key)
        if cached is not None:
            return cached

        merged_params = dict(self.config.default_params or {})
        if params:
            merged_params.update({k: v for k, v in params.items() if v not in (None, "")})

        try:
            response = self.session.get(
                f"{self.config.base_url}{path}",
                params=merged_params,
                timeout=self.config.timeout,
                headers={"User-Agent": "ColaboraPANC/1.0"},
            )
            response.raise_for_status()
            payload = response.json()
            cache.set(key, payload, self.config.cache_ttl)
            return payload
        except Exception as exc:
            logger.warning("Falha HTTP em %s%s: %s", self.config.base_url, path, exc)
            return {}
