from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from django.utils import timezone

from mapping.models import PontoPANC, EnriquecimentoTaxonomicoHistorico

from .providers import (
    GBIFProvider,
    GlobalNamesVerifierProvider,
    INaturalistProvider,
    TrefleProvider,
    TropicosProvider,
)


@dataclass
class EnrichmentResult:
    status: str
    data: dict[str, Any]
    fontes: list[str]
    payload_resumido: dict[str, Any]


class PlantEnrichmentOrchestrator:
    def __init__(self):
        self.gnv = GlobalNamesVerifierProvider()
        self.tropicos = TropicosProvider()
        self.gbif = GBIFProvider()
        self.inat = INaturalistProvider()
        self.trefle = TrefleProvider()

    def enrich_name(self, scientific_name: str, *, include_trefle: bool = False) -> EnrichmentResult:
        scientific_name = (scientific_name or "").strip()
        if not scientific_name:
            return EnrichmentResult(status="pendente", data={}, fontes=[], payload_resumido={})

        payloads: dict[str, dict[str, Any]] = {}
        fontes: list[str] = []

        gnv = self.gnv.validate_name(scientific_name)
        if gnv:
            payloads["global_names"] = gnv
            fontes.append("Global Names Verifier")

        base_name = gnv.get("nome_cientifico_validado") or scientific_name

        tropicos = self.tropicos.resolve(base_name)
        if tropicos:
            payloads["tropicos"] = tropicos
            fontes.append("Tropicos")

        gbif = self.gbif.fetch(base_name)
        if gbif:
            payloads["gbif"] = gbif
            fontes.append("GBIF")

        inat = self.inat.fetch(base_name)
        if inat:
            payloads["inaturalist"] = inat
            fontes.append("iNaturalist")

        if include_trefle:
            trefle = self.trefle.fetch_optional(base_name)
            if trefle:
                payloads["trefle"] = trefle
                fontes.append("Trefle")

        merged = self._merge_payloads(scientific_name, payloads)
        status = "validado" if len(fontes) >= 3 else ("parcial" if fontes else "pendente")

        return EnrichmentResult(
            status=status,
            data=merged,
            fontes=fontes,
            payload_resumido={k: {kk: vv for kk, vv in v.items() if kk != "raw"} for k, v in payloads.items()},
        )

    def enrich_ponto(self, ponto: PontoPANC, *, include_trefle: bool = False) -> EnrichmentResult:
        nome_cientifico = (
            ponto.nome_cientifico_sugerido
            or (ponto.planta.nome_cientifico if ponto.planta else "")
            or ponto.nome_popular
        )
        result = self.enrich_name(nome_cientifico, include_trefle=include_trefle)

        for field, value in result.data.items():
            if hasattr(ponto, field):
                setattr(ponto, field, value)

        ponto.status_enriquecimento = result.status
        ponto.fontes_enriquecimento = result.fontes
        ponto.payload_enriquecimento = result.payload_resumido
        ponto.ultima_validacao_em = timezone.now()
        ponto.enriquecimento_atualizado_em = timezone.now()
        ponto.save()

        EnriquecimentoTaxonomicoHistorico.objects.create(
            ponto=ponto,
            status=result.status,
            grau_confianca=result.data.get("grau_confianca", 0),
            fontes=result.fontes,
            payload_resumido=result.payload_resumido,
            executado_em=timezone.now(),
        )
        return result

    def _merge_payloads(self, submitted_name: str, payloads: dict[str, dict[str, Any]]) -> dict[str, Any]:
        merged: dict[str, Any] = {
            "nome_cientifico_submetido": submitted_name,
            "nome_cientifico_validado": submitted_name,
            "nome_aceito": "",
            "sinonimos": [],
            "autoria": "",
            "fonte_taxonomica_primaria": "",
            "fontes_secundarias": [],
            "grau_confianca": 0.0,
            "distribuicao_resumida": "",
            "ocorrencias_gbif": 0,
            "ocorrencias_inaturalist": 0,
            "fenologia_observada": "",
            "imagem_url": "",
            "imagem_fonte": "",
            "licenca_imagem": "",
        }

        # Priorização: Global Names + Tropicos para taxonomia
        tax_sources = [payloads.get("global_names", {}), payloads.get("tropicos", {})]
        for source in tax_sources:
            for key in ["nome_cientifico_validado", "nome_aceito", "autoria", "fonte_taxonomica_primaria"]:
                if source.get(key):
                    merged[key] = source[key]
            if source.get("sinonimos"):
                merged["sinonimos"] = list(dict.fromkeys(source.get("sinonimos") or []))

        # Priorização: GBIF + iNaturalist para ocorrência e fenologia
        gbif = payloads.get("gbif", {})
        inat = payloads.get("inaturalist", {})
        merged["ocorrencias_gbif"] = int(gbif.get("ocorrencias_gbif") or 0)
        merged["ocorrencias_inaturalist"] = int(inat.get("ocorrencias_inaturalist") or 0)
        merged["fenologia_observada"] = inat.get("fenologia_observada") or ""
        merged["distribuicao_resumida"] = gbif.get("distribuicao_resumida") or payloads.get("tropicos", {}).get("distribuicao_resumida", "")

        for source in (gbif, inat):
            if source.get("imagem_url") and not merged.get("imagem_url"):
                merged["imagem_url"] = source["imagem_url"]
                merged["imagem_fonte"] = source.get("imagem_fonte") or ""
                merged["licenca_imagem"] = source.get("licenca_imagem") or ""

        secondary_sources = []
        for key in ("tropicos", "gbif", "inaturalist", "trefle"):
            secondary_sources.extend(payloads.get(key, {}).get("fontes_secundarias", []))
        merged["fontes_secundarias"] = list(dict.fromkeys(secondary_sources))

        gnv_score = float(payloads.get("global_names", {}).get("grau") or 0)
        tax_strength = 0.35 if payloads.get("tropicos") else 0
        occ_strength = 0.35 if (merged["ocorrencias_gbif"] or merged["ocorrencias_inaturalist"]) else 0
        merged["grau_confianca"] = round(min(1.0, gnv_score * 0.3 + tax_strength + occ_strength), 2)

        return merged
