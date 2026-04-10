import re
from dataclasses import dataclass
from typing import Any

_MONTH_PATTERNS = {
    "jan": "jan",
    "janeiro": "jan",
    "fev": "fev",
    "fevereiro": "fev",
    "mar": "mar",
    "março": "mar",
    "marco": "mar",
    "abr": "abr",
    "abril": "abr",
    "mai": "mai",
    "maio": "mai",
    "jun": "jun",
    "junho": "jun",
    "jul": "jul",
    "julho": "jul",
    "ago": "ago",
    "agosto": "ago",
    "set": "set",
    "setembro": "set",
    "out": "out",
    "outubro": "out",
    "nov": "nov",
    "novembro": "nov",
    "dez": "dez",
    "dezembro": "dez",
}

_EDIBLE_PARTS = {
    "folha": "folha",
    "folhas": "folha",
    "fruto": "fruto",
    "frutos": "fruto",
    "flor": "flor",
    "flores": "flor",
    "raiz": "raiz",
    "raízes": "raiz",
    "semente": "semente",
    "sementes": "semente",
    "caule": "caule",
    "caules": "caule",
    "broto": "broto",
    "brotos": "broto",
    "tubérculo": "tubérculo",
    "tuberculo": "tubérculo",
    "tubérculos": "tubérculo",
    "tuberculos": "tubérculo",
    "bulbo": "bulbo",
    "bulbos": "bulbo",
    "casca": "casca",
    "cascas": "casca",
}

_NEGATIVE_EDIBLE_PATTERNS = [
    re.compile(r"\bn[aã]o\s+(?:é\s+)?comest[íi]vel\b", re.IGNORECASE),
    re.compile(r"\bincomest[íi]vel\b", re.IGNORECASE),
    re.compile(r"\bt[oó]xic[ao]\b", re.IGNORECASE),
]

_POSITIVE_EDIBLE_PATTERNS = [
    re.compile(r"\bé\s+comest[íi]vel\b", re.IGNORECASE),
    re.compile(r"\bplanta\s+comest[íi]vel\b", re.IGNORECASE),
    re.compile(r"\b(?:fruto|folha|raiz|flor|semente|caule)s?\s+comest[íi]veis\b", re.IGNORECASE),
]


@dataclass
class ExtractedField:
    value: Any
    confirmed: bool
    evidence: str


def _clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "")).strip()


def _sentence_candidates(text: str) -> list[str]:
    normalized = _clean_text(text)
    if not normalized:
        return []
    return [s.strip() for s in re.split(r"(?<=[\.!?;])\s+", normalized) if s.strip()]


def extract_comestivel(text: str) -> ExtractedField:
    sentences = _sentence_candidates(text)
    for sentence in sentences:
        if any(pattern.search(sentence) for pattern in _NEGATIVE_EDIBLE_PATTERNS):
            return ExtractedField(value="Não", confirmed=True, evidence=sentence[:220])
        if any(pattern.search(sentence) for pattern in _POSITIVE_EDIBLE_PATTERNS):
            return ExtractedField(value="Sim", confirmed=True, evidence=sentence[:220])
    return ExtractedField(value="Não informado", confirmed=False, evidence="conteúdo insuficiente")


def extract_parte_comestivel(text: str) -> ExtractedField:
    lowered = _clean_text(text).lower()
    found: list[str] = []
    for token, normalized in _EDIBLE_PARTS.items():
        if re.search(rf"\b{re.escape(token)}\b", lowered):
            found.append(normalized)
    unique = sorted(set(found))
    if not unique:
        return ExtractedField(value="Não informado", confirmed=False, evidence="conteúdo insuficiente")
    return ExtractedField(value=", ".join(unique), confirmed=True, evidence=f"partes detectadas: {', '.join(unique)}")


def _extract_months(text: str) -> list[str]:
    lowered = _clean_text(text).lower()
    found: list[str] = []
    for raw, normalized in _MONTH_PATTERNS.items():
        if re.search(rf"\b{re.escape(raw)}\b", lowered):
            found.append(normalized)
    order = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]
    return [m for m in order if m in set(found)]


def extract_frutificacao(text: str) -> ExtractedField:
    sentences = [s for s in _sentence_candidates(text) if re.search(r"frutifica|frutificação|frutificaç[aã]o", s, re.IGNORECASE)]
    search_space = " ".join(sentences) if sentences else text
    months = _extract_months(search_space)
    if not months:
        return ExtractedField(value="Não informado", confirmed=False, evidence="conteúdo insuficiente")
    return ExtractedField(value=", ".join(months), confirmed=True, evidence=(sentences[0][:220] if sentences else f"meses detectados: {', '.join(months)}"))


def extract_colheita(text: str) -> ExtractedField:
    sentences = [s for s in _sentence_candidates(text) if re.search(r"colheita|colher|safra", s, re.IGNORECASE)]
    search_space = " ".join(sentences) if sentences else text
    months = _extract_months(search_space)
    if months:
        return ExtractedField(value=", ".join(months), confirmed=True, evidence=(sentences[0][:220] if sentences else f"meses detectados: {', '.join(months)}"))
    if sentences:
        short = sentences[0][:120]
        return ExtractedField(value=short, confirmed=True, evidence=short)
    return ExtractedField(value="Não informado", confirmed=False, evidence="conteúdo insuficiente")
