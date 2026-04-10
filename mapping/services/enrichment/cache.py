import hashlib
import json
from typing import Any

from django.core.cache import cache


class EnrichmentCache:
    def __init__(self, ttl_seconds: int = 3600):
        self.ttl_seconds = ttl_seconds

    def build_key(self, namespace: str, payload: dict[str, Any]) -> str:
        digest = hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()
        return f"enrichment:{namespace}:{digest}"

    def get(self, namespace: str, payload: dict[str, Any]) -> Any:
        return cache.get(self.build_key(namespace, payload))

    def set(self, namespace: str, payload: dict[str, Any], value: Any, ttl_seconds: int | None = None) -> None:
        cache.set(self.build_key(namespace, payload), value, ttl_seconds or self.ttl_seconds)
