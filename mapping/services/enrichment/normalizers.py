from __future__ import annotations

import re
from typing import Any

from .harvest_rules import calcular_colheita_periodo

MESES_PT = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]
EDIBLE_PART_MAP = {
    "root": "raiz",
    "roots": "raiz",
    "raiz": "raiz",
    "raízes": "raiz",
    "stem": "caule",
    "stems": "caule",
    "caule": "caule",
    "caules": "caule",
    "leaf": "folha",
    "leaves": "folha",
    "folha": "folha",
    "folhas": "folha",
    "flower": "flor",
    "flowers": "flor",
    "flor": "flor",
    "flores": "flor",
    "fruit": "fruto",
    "fruits": "fruto",
    "fruto": "fruto",
    "frutos": "fruto",
    "seed": "semente",
    "seeds": "semente",
    "semente": "semente",
    "sementes": "semente",
    "tuber": "tubérculo",
    "tubers": "tubérculo",
    "tubérculo": "tubérculo",
    "tuberculo": "tubérculo",
    "tubérculos": "tubérculo",
    "tuberculos": "tubérculo",
    "shoot": "broto",
    "shoots": "broto",
    "broto": "broto",
    "brotos": "broto",
    "bulb": "bulbo",
    "bulbs": "bulbo",
    "bulbo": "bulbo",
    "bulbos": "bulbo",
    "bark": "casca",
    "casca": "casca",
    "cascas": "casca",
}


def _month_list(values: list[str | int] | None) -> list[str]:
    if not values:
        return []
    out: list[str] = []
    for value in values:
        text = str(value).strip().lower()
        if text.isdigit() and 1 <= int(text) <= 12:
            out.append(MESES_PT[int(text) - 1])
            continue
        if text[:3] in MESES_PT:
            out.append(text[:3])
    return list(dict.fromkeys(out))


def _normalize_edible_parts(value: Any) -> list[str]:
    if value is None:
        return []
    raw: list[str]
    if isinstance(value, list):
        raw = [str(item).strip().lower() for item in value if str(item).strip()]
    else:
        text = str(value).strip().lower()
        raw = [part.strip() for part in text.replace("/", ",").split(",") if part.strip()]

    mapped = [EDIBLE_PART_MAP.get(item, item) for item in raw]
    allowed = {"raiz", "caule", "folha", "flor", "fruto", "semente", "tubérculo", "broto", "bulbo", "casca"}
    return list(dict.fromkeys(item for item in mapped if item in allowed))


def _comestibilidade(trefle: dict[str, Any]) -> tuple[str, bool, str]:
    edible = trefle.get("comestivel")
    if edible is True:
        return "sim", True, "Trefle"
    if edible is False:
        return "nao", True, "Trefle"
    return "indeterminado", False, "nenhuma_fonte_confirmou"


def _comestibilidade_wikipedia(wikipedia: dict[str, Any]) -> tuple[str, bool, str]:
    fields = wikipedia.get("fields") or {}
    item = fields.get("comestivel") or {}
    if not item.get("confirmed"):
        return "indeterminado", False, "nenhuma_fonte_confirmou"

    value = str(item.get("value") or "").strip().lower()
    if value == "sim":
        return "sim", True, "Wikipedia/Wikimedia"
    if value == "não" or value == "nao":
        return "nao", True, "Wikipedia/Wikimedia"
    return "indeterminado", False, "nenhuma_fonte_confirmou"


def _comestibilidade_gbif(gbif: dict[str, Any]) -> tuple[str, bool, str]:
    """Infere comestibilidade a partir da descrição do GBIF (kingdom=Plantae + ocorrências altas)."""
    if not gbif.get("ok"):
        return "indeterminado", False, "nenhuma_fonte_confirmou"
    raw_match = (gbif.get("raw") or {}).get("match") or {}
    kingdom = (raw_match.get("kingdom") or "").strip().lower()
    # GBIF não fornece comestibilidade diretamente; não inferir
    return "indeterminado", False, "nenhuma_fonte_confirmou"


def _comestibilidade_inat(inat: dict[str, Any]) -> tuple[str, bool, str]:
    """iNaturalist não fornece comestibilidade diretamente."""
    return "indeterminado", False, "nenhuma_fonte_confirmou"


def _parte_comestivel_wikipedia(wikipedia: dict[str, Any]) -> list[str]:
    wiki_part = ((wikipedia.get("fields") or {}).get("parte_comestivel") or {})
    if wiki_part.get("confirmed") and wiki_part.get("value") and str(wiki_part.get("value")).strip().lower() != "não informado":
        return _normalize_edible_parts(str(wiki_part.get("value")))
    return []


def _frutificacao_wikipedia(wikipedia: dict[str, Any]) -> list[str]:
    wiki_fruit = ((wikipedia.get("fields") or {}).get("frutificacao") or {})
    if wiki_fruit.get("confirmed") and wiki_fruit.get("value"):
        return _month_list(str(wiki_fruit.get("value")).split(","))
    return []


def _colheita_wikipedia(wikipedia: dict[str, Any]) -> list[str] | str | None:
    wiki_harvest = ((wikipedia.get("fields") or {}).get("colheita") or {})
    raw = str(wiki_harvest.get("value") or "")
    if wiki_harvest.get("confirmed") and raw and raw.lower() != "não informado":
        wiki_months = _month_list(raw.split(","))
        return wiki_months if wiki_months else raw[:120]
    return None


def consolidar_resultados(
    scientific_name: str,
    gnv: dict[str, Any],
    tropicos: dict[str, Any],
    gbif: dict[str, Any],
    inat: dict[str, Any],
    trefle: dict[str, Any] | None = None,
    wikipedia: dict[str, Any] | None = None,
) -> dict[str, Any]:
    trefle = trefle or {}
    wikipedia = wikipedia or {}

    nome_validado = gnv.get("nome_cientifico_validado") or scientific_name
    nome_aceito = tropicos.get("nome_aceito") or gnv.get("nome_aceito") or nome_validado

    conflito_taxonomico = bool(
        gnv.get("nome_aceito") and tropicos.get("nome_aceito") and gnv.get("nome_aceito") != tropicos.get("nome_aceito")
    )

    comestibilidade_status = "indeterminado"
    comestibilidade_confirmada = False
    comestibilidade_fonte = "nenhuma_fonte_confirmou"
    for resolver in (
        lambda: _comestibilidade(trefle),
        lambda: _comestibilidade_wikipedia(wikipedia),
        lambda: _comestibilidade_gbif(gbif),
        lambda: _comestibilidade_inat(inat),
    ):
        status, confirmed, fonte = resolver()
        if confirmed:
            comestibilidade_status = status
            comestibilidade_confirmada = True
            comestibilidade_fonte = fonte
            break

    # Se nenhuma fonte confirmou diretamente, mas Trefle retornou partes comestíveis,
    # infere-se que a planta é comestível
    edible_parts: list[str] = []
    for resolver in (
        lambda: _normalize_edible_parts(trefle.get("edible_part")),
        lambda: _parte_comestivel_wikipedia(wikipedia),
    ):
        candidate = resolver()
        if candidate:
            edible_parts = candidate
            break
    parte_comestivel_confirmada = bool(edible_parts)

    # Inferência: se há partes comestíveis mas comestibilidade ficou indeterminada, inferir "sim"
    if not comestibilidade_confirmada and parte_comestivel_confirmada:
        comestibilidade_status = "sim"
        comestibilidade_confirmada = True
        comestibilidade_fonte = "inferido (partes comestíveis detectadas)"

    fruta_meses: list[str] = []
    for resolver in (
        lambda: _month_list(trefle.get("fruit_months") or []),
        lambda: _month_list(inat.get("fruit_months") or []),
        lambda: _frutificacao_wikipedia(wikipedia),
    ):
        candidate = resolver()
        if candidate:
            fruta_meses = candidate
            break
    frutificacao_confirmada = bool(fruta_meses)

    colheita_periodo_raw = calcular_colheita_periodo(
        planting_days_to_harvest=trefle.get("planting_days_to_harvest"),
        days_to_harvest=trefle.get("days_to_harvest"),
        growth_months=trefle.get("growth_months"),
        fruit_months=trefle.get("fruit_months"),
        bloom_months=trefle.get("bloom_months"),
    )
    colheita_confirmada = colheita_periodo_raw != "nao_informado"
    if not colheita_confirmada:
        wiki_colheita = _colheita_wikipedia(wikipedia)
        if wiki_colheita:
            colheita_periodo_raw = wiki_colheita
            colheita_confirmada = True

    fontes_campos = {
        "comestibilidade_status": comestibilidade_fonte,
        "parte_comestivel": "Trefle" if parte_comestivel_confirmada and trefle.get("edible_part") else ("Wikipedia/Wikimedia" if parte_comestivel_confirmada else "nenhuma_fonte_confirmou"),
        "frutificacao_meses": "Trefle" if frutificacao_confirmada and trefle.get("fruit_months") else ("iNaturalist" if frutificacao_confirmada and inat.get("fruit_months") else ("Wikipedia/Wikimedia" if frutificacao_confirmada else "nenhuma_fonte_confirmou")),
        "colheita_periodo": "Trefle" if colheita_confirmada and colheita_periodo_raw != "nao_informado" and bool(trefle) else ("Wikipedia/Wikimedia" if colheita_confirmada else "nenhuma_fonte_confirmou"),
    }

    fenologia_obs = inat.get("fenologia_observada") or (", ".join(fruta_meses) if fruta_meses else "") or ""

    image_from_gbif = bool(gbif.get("imagem_url"))
    image_from_inat = bool(inat.get("imagem_url"))

    fontes_sec = []
    if gbif.get("ok"):
        fontes_sec.append("GBIF")
    if inat.get("ok"):
        fontes_sec.append("iNaturalist")
    if trefle.get("ok"):
        fontes_sec.append("Trefle")

    gbif_match = (gbif.get("raw") or {}).get("match") if isinstance(gbif.get("raw"), dict) else {}
    gbif_match = gbif_match if isinstance(gbif_match, dict) else {}
    raw_extract = ((wikipedia.get("raw") or {}).get("extract") if isinstance(wikipedia.get("raw"), dict) else "") or ""
    descricao_consolidada = re.sub(r"\[[0-9]+\]", "", raw_extract or "").strip()
    descricao_consolidada = re.sub(r"\s+", " ", descricao_consolidada)

    return {
        "nome_cientifico_submetido": scientific_name,
        "nome_cientifico_validado": nome_validado,
        "nome_aceito": nome_aceito,
        "autoria": tropicos.get("autoria") or gnv.get("autoria") or "",
        "sinonimos": list(dict.fromkeys(tropicos.get("sinonimos") or [])),
        "fonte_taxonomica_primaria": tropicos.get("fonte_taxonomica_primaria") or gnv.get("fonte_taxonomica_primaria") or "",
        "fontes_taxonomicas_secundarias": fontes_sec,
        "distribuicao_resumida": gbif.get("distribuicao_resumida") or tropicos.get("distribuicao_resumida") or "",
        "ocorrencias_gbif": int(gbif.get("ocorrencias_gbif") or 0),
        "ocorrencias_inaturalist": int(inat.get("ocorrencias_inaturalist") or 0),
        "fenologia_observada": fenologia_obs,
        "imagem_url": gbif.get("imagem_url") if image_from_gbif else (inat.get("imagem_url") if image_from_inat else ""),
        "imagem_fonte": gbif.get("imagem_fonte") if image_from_gbif else (inat.get("imagem_fonte") if image_from_inat else ""),
        "licenca_imagem": gbif.get("licenca_imagem") if image_from_gbif else (inat.get("licenca_imagem") if image_from_inat else ""),
        "comestibilidade_status": comestibilidade_status,
        "comestibilidade_confirmada": comestibilidade_confirmada,
        "parte_comestivel": edible_parts or None,
        "parte_comestivel_confirmada": parte_comestivel_confirmada,
        "frutificacao_meses": fruta_meses or None,
        "frutificacao_confirmada": frutificacao_confirmada,
        "colheita_periodo": colheita_periodo_raw if colheita_confirmada else None,
        "colheita_confirmada": colheita_confirmada,
        "fontes_campos_enriquecimento": fontes_campos,
        "status_validacao_campos": {
            "comestibilidade_status": "confirmado" if comestibilidade_confirmada else "indeterminado",
            "parte_comestivel": "confirmado" if parte_comestivel_confirmada else "indeterminado",
            "frutificacao_meses": "confirmado" if frutificacao_confirmada else "indeterminado",
            "colheita_periodo": "confirmado" if colheita_confirmada else "indeterminado",
        },
        "conflito_taxonomico": conflito_taxonomico,
        "dados_auxiliares_trefle": {
            "growth_months": trefle.get("growth_months"),
            "fruit_months": trefle.get("fruit_months"),
            "bloom_months": trefle.get("bloom_months"),
            "days_to_harvest": trefle.get("days_to_harvest"),
            "planting_days_to_harvest": trefle.get("planting_days_to_harvest"),
        },
        "familia": (gbif_match.get("family") or tropicos.get("distribuicao_resumida") or "").strip(),
        "genero": (gbif_match.get("genus") or "").strip(),
        "especie": (gbif_match.get("species") or "").strip(),
        "toxicidade": str(trefle.get("toxicity") or "").strip(),
        "descricao_consolidada": descricao_consolidada,
        "descricao_resumida": descricao_consolidada[:500],
    }
