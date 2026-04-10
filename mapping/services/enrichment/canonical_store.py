from __future__ import annotations

from typing import Any

from django.db.models import Q
from django.utils import timezone

from mapping.models import PlantaAlias, PlantaReferencial
from .search_terms import dedupe_names, normalize_text


class CanonicalPlantStore:
    """Persistência da ficha canônica local e deduplicação por alias."""

    @staticmethod
    def find_existing(*, scientific_name: str = "", popular_name: str = "", aliases: list[str] | None = None) -> PlantaReferencial | None:
        aliases = aliases or []
        q = Q()
        if scientific_name:
            q |= Q(nome_cientifico__iexact=scientific_name)
            q |= Q(nome_cientifico_validado__iexact=scientific_name)
            q |= Q(nome_aceito__iexact=scientific_name)
        if popular_name:
            q |= Q(nome_popular__iexact=popular_name)
        if q:
            found = PlantaReferencial.objects.filter(q).first()
            if found:
                return found

        normalized_aliases = [normalize_text(name) for name in aliases if name]
        if normalized_aliases:
            alias = PlantaAlias.objects.filter(normalized_name__in=normalized_aliases).select_related("planta").first()
            if alias:
                return alias.planta
        return None

    @staticmethod
    def persist_from_enrichment(planta: PlantaReferencial, consolidated: dict[str, Any], *, fontes_ok: list[str], aliases: list[str], confidence: float) -> PlantaReferencial:
        planta.nome_cientifico = consolidated.get("nome_aceito") or consolidated.get("nome_cientifico_validado") or planta.nome_cientifico
        planta.nome_cientifico_submetido = consolidated.get("nome_cientifico_submetido") or planta.nome_cientifico_submetido
        planta.nome_cientifico_validado = consolidated.get("nome_cientifico_validado") or planta.nome_cientifico_validado
        planta.nome_aceito = consolidated.get("nome_aceito") or planta.nome_aceito
        planta.autoria = consolidated.get("autoria") or planta.autoria
        planta.sinonimos = dedupe_names((planta.sinonimos or []) + (consolidated.get("sinonimos") or []))
        planta.nomes_populares = dedupe_names((planta.nomes_populares or []) + (consolidated.get("nomes_populares") or []))
        planta.aliases = dedupe_names((planta.aliases or []) + aliases + planta.sinonimos + planta.nomes_populares)
        planta.familia = consolidated.get("familia") or planta.familia
        planta.genero = consolidated.get("genero") or planta.genero
        planta.especie = consolidated.get("especie") or planta.especie
        planta.distribuicao_resumida = consolidated.get("distribuicao_resumida") or planta.distribuicao_resumida
        planta.imagem_url = consolidated.get("imagem_url") or planta.imagem_url
        planta.imagem_fonte = consolidated.get("imagem_fonte") or planta.imagem_fonte
        planta.licenca_imagem = consolidated.get("licenca_imagem") or planta.licenca_imagem
        planta.toxicidade = consolidated.get("toxicidade") or planta.toxicidade
        planta.descricao_consolidada = consolidated.get("descricao_consolidada") or planta.descricao_consolidada
        planta.descricao_resumida = consolidated.get("descricao_resumida") or planta.descricao_resumida
        planta.comestivel = True if consolidated.get("comestibilidade_status") == "sim" else (False if consolidated.get("comestibilidade_status") == "nao" else planta.comestivel)
        if consolidated.get("parte_comestivel"):
            planta.parte_comestivel = ", ".join(consolidated["parte_comestivel"])
        if consolidated.get("frutificacao_meses"):
            planta.epoca_frutificacao = ", ".join(consolidated["frutificacao_meses"])
            planta.sazonalidade = {**(planta.sazonalidade or {}), "frutificacao": consolidated["frutificacao_meses"]}
        if consolidated.get("colheita_periodo"):
            colheita = consolidated["colheita_periodo"]
            planta.epoca_colheita = ", ".join(colheita) if isinstance(colheita, list) else str(colheita)
            planta.sazonalidade = {**(planta.sazonalidade or {}), "colheita": colheita}

        planta.fontes_utilizadas = dedupe_names((planta.fontes_utilizadas or []) + (fontes_ok or []))
        planta.nivel_confianca_enriquecimento = max(float(planta.nivel_confianca_enriquecimento or 0), float(confidence or 0))
        planta.status_enriquecimento = consolidated.get("status_enriquecimento", planta.status_enriquecimento or "parcial")
        planta.ultima_validacao_em = timezone.now()

        has_taxonomy = bool(planta.nome_cientifico and (planta.nome_cientifico_validado or planta.nome_aceito))
        has_description = bool(planta.descricao_consolidada or planta.distribuicao_resumida)
        has_minimum_traits = bool(planta.comestivel is not None or planta.parte_comestivel or planta.epoca_frutificacao or planta.epoca_colheita)
        planta.is_fully_enriched = bool(has_taxonomy and has_description and has_minimum_traits)
        if planta.is_fully_enriched:
            planta.enriquecimento_completo_em = timezone.now()

        planta.save()

        for alias_name in planta.aliases:
            normalized = normalize_text(alias_name)
            if not normalized:
                continue
            PlantaAlias.objects.update_or_create(
                planta=planta,
                normalized_name=normalized,
                defaults={"name": alias_name, "source": "enrichment_pipeline"},
            )
        return planta
