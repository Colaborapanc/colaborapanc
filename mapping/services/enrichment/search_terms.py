from __future__ import annotations

import re
import unicodedata
from typing import Iterable


def normalize_text(value: str) -> str:
    base = unicodedata.normalize("NFKD", value or "").encode("ascii", "ignore").decode("ascii")
    return re.sub(r"\s+", " ", base).strip().lower()


def strip_authorship(value: str) -> str:
    text = (value or "").strip()
    # Remove autoria botânica após binômio/trinômio
    parts = text.split()
    if len(parts) <= 2:
        return text
    kept = []
    for part in parts:
        if not kept:
            kept.append(part)
            continue
        if len(kept) == 1:
            kept.append(part)
            continue
        break
    return " ".join(kept).strip()


def safe_variants(value: str) -> list[str]:
    raw = (value or "").strip()
    if not raw:
        return []
    variants = [raw]
    without_author = strip_authorship(raw)
    if without_author and without_author != raw:
        variants.append(without_author)
    normalized = normalize_text(raw)
    if normalized and normalized != normalize_text(without_author):
        variants.append(normalized)
    if "-" in raw:
        variants.append(raw.replace("-", " "))
    if "," in raw:
        variants.append(raw.split(",")[0].strip())
    return dedupe_names(variants)


def dedupe_names(items: Iterable[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for item in items:
        value = (item or "").strip()
        if not value:
            continue
        key = normalize_text(value)
        if key in seen:
            continue
        seen.add(key)
        out.append(value)
    return out


def build_progressive_search_terms(*, submitted_scientific: str = "", validated_scientific: str = "", accepted_name: str = "", canonical_name: str = "", current_name: str = "", synonyms: Iterable[str] | None = None, popular_names: Iterable[str] | None = None, aliases: Iterable[str] | None = None) -> list[str]:
    ordered: list[str] = [
        submitted_scientific,
        validated_scientific,
        accepted_name,
        canonical_name,
        current_name,
    ]
    ordered.extend(list(synonyms or []))
    ordered.extend(list(popular_names or []))
    ordered.extend(list(aliases or []))

    expanded: list[str] = []
    for name in ordered:
        expanded.extend(safe_variants(name))
    return dedupe_names(expanded)
