import hashlib
import json
import re
import unicodedata
from typing import Any


_SAFE_CHARS_PATTERN = re.compile(r"[^a-z0-9_-]+")


def _normalize_part(value: Any) -> str:
    raw = "" if value is None else str(value).strip().lower()
    if not raw:
        return "none"
    normalized = unicodedata.normalize("NFKD", raw).encode("ascii", "ignore").decode("ascii")
    cleaned = _SAFE_CHARS_PATTERN.sub("-", normalized).strip("-")
    return cleaned or "none"


def build_safe_cache_key(prefix: str, *parts: Any, max_prefix_size: int = 80) -> str:
    """
    Gera chave segura para backends como memcached:
    - somente caracteres [a-z0-9_-] no prefixo semântico;
    - hash SHA-256 dos parâmetros completos para manter unicidade;
    - tamanho estável e previsível.
    """
    normalized_prefix = _normalize_part(prefix)[:max_prefix_size]
    payload = json.dumps([parts], sort_keys=True, default=str, ensure_ascii=True)
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24]
    return f"cp:{normalized_prefix}:{digest}"
