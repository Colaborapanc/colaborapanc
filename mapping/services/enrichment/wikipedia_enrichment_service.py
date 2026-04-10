import logging
import re
import unicodedata
from dataclasses import dataclass
from typing import Any

from django.conf import settings

from mapping.services.external.wikimedia_client import WikimediaClient

from .field_extractors import (
    ExtractedField,
    extract_colheita,
    extract_comestivel,
    extract_frutificacao,
    extract_parte_comestivel,
)

logger = logging.getLogger(__name__)


@dataclass
class ResolvedPage:
    title: str
    language: str
    confidence: float
    evidence: str


class WikipediaEnrichmentService:
    source_name = "wikimedia"

    def __init__(self):
        self.client = WikimediaClient()
        self.min_confidence = float(getattr(settings, "WIKIMEDIA_MIN_MATCH_CONFIDENCE", 0.55))
        self.fallback_languages = ["pt", "en"]

    @staticmethod
    def _normalize(text: str) -> str:
        base = unicodedata.normalize("NFKD", (text or "")).encode("ascii", "ignore").decode("ascii")
        return re.sub(r"\s+", " ", base).strip().lower()

    def _build_queries(self, scientific_valid: str | None, scientific_suggested: str | None, popular: str | None) -> list[str]:
        ordered = [scientific_valid, scientific_suggested, popular]
        out: list[str] = []
        seen = set()
        for raw in ordered:
            value = (raw or "").strip()
            if not value:
                continue
            normalized = self._normalize(value)
            if normalized in seen:
                continue
            seen.add(normalized)
            out.append(value)
            if "(" in value:
                out.append(value.split("(")[0].strip())
            if "," in value:
                out.append(value.split(",")[0].strip())
        return [q for q in out if q]

    def _candidate_score(self, *, query: str, title: str, snippet: str) -> tuple[float, str]:
        normalized_query = self._normalize(query)
        normalized_title = self._normalize(title)
        normalized_snippet = self._normalize(snippet)

        if "desambiguacao" in normalized_snippet or "disambiguation" in normalized_snippet:
            return 0.0, "pagina_desambiguacao"

        score = 0.0
        if normalized_query == normalized_title:
            score += 0.75
        elif normalized_query in normalized_title:
            score += 0.55
        elif normalized_title in normalized_query:
            score += 0.4

        query_terms = set(normalized_query.split())
        title_terms = set(normalized_title.split())
        if query_terms and title_terms:
            overlap = len(query_terms & title_terms) / len(query_terms)
            score += min(overlap * 0.25, 0.25)

        if "planta" in normalized_snippet or "species of plant" in normalized_snippet:
            score += 0.1
        if "genero" in normalized_snippet or "especie" in normalized_snippet:
            score += 0.05

        return min(score, 1.0), "ok"

    def resolve_page(self, *, scientific_valid: str | None, scientific_suggested: str | None, popular_name: str | None) -> dict[str, Any]:
        queries = self._build_queries(scientific_valid, scientific_suggested, popular_name)
        best_page: ResolvedPage | None = None
        attempts: list[dict[str, Any]] = []
        last_error = None

        for language in self.fallback_languages:
            for query in queries:
                results, error = self.client.search_page_candidates(query=query, language=language, limit=5)
                if error:
                    last_error = self.client.classify_error(error)
                for candidate in results:
                    title = candidate.get("title") or ""
                    snippet = re.sub(r"<[^>]+>", " ", candidate.get("snippet") or "")
                    score, reason = self._candidate_score(query=query, title=title, snippet=snippet)
                    attempts.append({"query": query, "language": language, "title": title, "score": round(score, 2), "reason": reason})
                    if score < self.min_confidence:
                        continue
                    if not best_page or score > best_page.confidence:
                        best_page = ResolvedPage(title=title, language=language, confidence=round(score, 2), evidence=f"query={query}")

        if not best_page:
            return {
                "ok": False,
                "error": last_error or "not_found",
                "error_type": "page_not_found" if (last_error in (None, "none")) else last_error,
                "attempts": attempts,
            }

        return {"ok": True, "page": best_page, "attempts": attempts}

    def _extract_fields(self, extract: str) -> dict[str, ExtractedField]:
        return {
            "comestivel": extract_comestivel(extract),
            "parte_comestivel": extract_parte_comestivel(extract),
            "frutificacao": extract_frutificacao(extract),
            "colheita": extract_colheita(extract),
        }

    def enrich_target_fields(self, *, scientific_valid: str | None, scientific_suggested: str | None, popular_name: str | None) -> dict[str, Any]:
        if not getattr(settings, "WIKIMEDIA_ENRICHMENT_ENABLED", True):
            return {"ok": False, "error": "disabled", "error_type": "disabled"}

        resolved = self.resolve_page(
            scientific_valid=scientific_valid,
            scientific_suggested=scientific_suggested,
            popular_name=popular_name,
        )
        if not resolved.get("ok"):
            return {**resolved, "status": "sem_dados"}

        page: ResolvedPage = resolved["page"]
        payload, error = self.client.fetch_page_extract(language=page.language, title=page.title)
        if error:
            return {
                "ok": False,
                "status": "erro_externo",
                "error": error,
                "error_type": self.client.classify_error(error),
                "attempts": resolved.get("attempts", []),
                "source": {"fonte": "wikimedia", "titulo": page.title, "idioma": page.language, "confianca": page.confidence},
            }

        pageprops = payload.get("pageprops") or {}
        if pageprops.get("disambiguation"):
            return {
                "ok": False,
                "status": "ambiguo",
                "error": "ambiguous_page",
                "error_type": "ambiguous_page",
                "attempts": resolved.get("attempts", []),
                "source": {"fonte": "wikimedia", "titulo": page.title, "idioma": page.language, "confianca": page.confidence},
            }

        extract = payload.get("extract") or ""
        if not extract.strip():
            return {
                "ok": False,
                "status": "conteudo_insuficiente",
                "error": "insufficient_content",
                "error_type": "insufficient_content",
                "attempts": resolved.get("attempts", []),
                "source": {"fonte": "wikimedia", "titulo": page.title, "idioma": page.language, "confianca": page.confidence},
            }

        fields = self._extract_fields(extract)

        return {
            "ok": True,
            "status": "ok",
            "source": {
                "fonte": "wikimedia",
                "titulo": page.title,
                "idioma": page.language,
                "confianca": page.confidence,
            },
            "attempts": resolved.get("attempts", []),
            "fields": {
                "comestivel": {"value": fields["comestivel"].value, "confirmed": fields["comestivel"].confirmed, "evidence": fields["comestivel"].evidence},
                "parte_comestivel": {"value": fields["parte_comestivel"].value, "confirmed": fields["parte_comestivel"].confirmed, "evidence": fields["parte_comestivel"].evidence},
                "frutificacao": {"value": fields["frutificacao"].value, "confirmed": fields["frutificacao"].confirmed, "evidence": fields["frutificacao"].evidence},
                "colheita": {"value": fields["colheita"].value, "confirmed": fields["colheita"].confirmed, "evidence": fields["colheita"].evidence},
            },
            "raw": {"extract": extract},
        }
