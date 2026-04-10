import logging
from typing import Any

from django.utils import timezone

from mapping.models import EnriquecimentoTaxonomicoHistorico, PontoPANC
from mapping.services.biodiversity.gbif import GBIFService
from mapping.services.biodiversity.inaturalist import INaturalistService
from mapping.services.taxonomy.global_names import GlobalNamesService
from mapping.services.taxonomy.tropicos import TropicosService
from mapping.services.traits.trefle import TrefleTraitsService
from mapping.services.enrichment.wikipedia_enrichment_service import WikipediaEnrichmentService

from .canonical_store import CanonicalPlantStore
from .confidence import calcular_grau_confianca_taxonomica, definir_status_enriquecimento
from .normalizers import consolidar_resultados
from .search_terms import build_progressive_search_terms, dedupe_names

logger = logging.getLogger(__name__)


class PlantaEnrichmentPipeline:
    def __init__(self):
        self.gnv = GlobalNamesService()
        self.tropicos = TropicosService()
        self.gbif = GBIFService()
        self.inat = INaturalistService()
        self.trefle = TrefleTraitsService()
        self.wikipedia = WikipediaEnrichmentService()
        self.canonical_store = CanonicalPlantStore()

    def run_for_ponto(self, ponto: PontoPANC, *, include_trefle: bool = True, origem: str = "cadastro") -> dict[str, Any]:
        logger.info(
            "Pipeline enriquecimento iniciado ponto=%s origem=%s include_trefle=%s",
            ponto.id,
            origem,
            include_trefle,
        )
        if ponto.planta_id and getattr(ponto.planta, "is_fully_enriched", False):
            logger.info("Usando base canônica local (sem chamadas externas) ponto=%s planta=%s", ponto.id, ponto.planta_id)
            self._hydrate_from_canonical(ponto)
            return {
                "ok": True,
                "status_enriquecimento": ponto.status_enriquecimento,
                "fontes_ok": ["base_local"],
                "grau_confianca_taxonomica": ponto.grau_confianca_taxonomica,
                "used_local_canonical": True,
            }

        scientific_name = (
            ponto.nome_cientifico_sugerido
            or ponto.nome_cientifico_submetido
            or (ponto.planta.nome_cientifico if ponto.planta else "")
            or ""
        ).strip()

        if not scientific_name:
            scientific_name = self._resolve_scientific_from_popular(ponto)

        if not scientific_name:
            ponto.status_enriquecimento = "pendente"
            ponto.save(update_fields=["status_enriquecimento", "atualizado_em"])
            return {"ok": False, "status_enriquecimento": "pendente", "reason": "scientific_name_missing"}

        responses: dict[str, dict[str, Any]] = {}
        failures: dict[str, str] = {}
        trace_busca: dict[str, Any] = {"aliases": [], "consultas": []}
        seed_aliases = self._seed_aliases(ponto, scientific_name)

        # 1) Global Names Verifier (multichave/fallback)
        responses["global_names"], aliases_gnv = self._query_with_fallback(
            source="global_names",
            names=seed_aliases,
            query_fn=self.gnv.validate_name,
            trace_busca=trace_busca,
        )
        seed_aliases = dedupe_names(seed_aliases + aliases_gnv)
        logger.debug("Retorno Global Names Verifier ponto=%s ok=%s", ponto.id, responses["global_names"].get("ok"))
        if responses["global_names"].get("error"):
            failures["global_names"] = responses["global_names"]["error"]
        ambiguity = self._extract_taxonomic_ambiguity(responses["global_names"])

        # 2) Tropicos com aliases expandidos
        validated_name = responses["global_names"].get("nome_cientifico_validado") or scientific_name
        tax_aliases = build_progressive_search_terms(
            submitted_scientific=scientific_name,
            validated_scientific=validated_name,
            accepted_name=responses["global_names"].get("nome_aceito") or "",
            canonical_name=responses["global_names"].get("nome_cientifico_validado") or "",
            current_name=responses["global_names"].get("nome_aceito") or "",
            synonyms=responses["global_names"].get("sinonimos") or [],
            popular_names=[ponto.nome_popular or (ponto.planta.nome_popular if ponto.planta else "")],
            aliases=seed_aliases,
        )
        responses["tropicos"], aliases_tropicos = self._query_with_fallback(
            source="tropicos",
            names=tax_aliases,
            query_fn=self.tropicos.resolve,
            trace_busca=trace_busca,
        )
        seed_aliases = dedupe_names(seed_aliases + aliases_tropicos + (responses["tropicos"].get("sinonimos") or []))
        logger.debug("Retorno Tropicos ponto=%s ok=%s", ponto.id, responses["tropicos"].get("ok"))
        if responses["tropicos"].get("error"):
            failures["tropicos"] = responses["tropicos"]["error"]

        # 3..6) Demais integrações
        logger.debug("Chamando GBIF/iNaturalist/Trefle/Wikipedia ponto=%s com aliases=%s", ponto.id, len(seed_aliases))
        responses["gbif"], _ = self._query_with_fallback(source="gbif", names=seed_aliases, query_fn=self.gbif.fetch, trace_busca=trace_busca)
        responses["inaturalist"], _ = self._query_with_fallback(source="inaturalist", names=seed_aliases, query_fn=self.inat.fetch, trace_busca=trace_busca)
        responses["trefle"], _ = self._query_with_fallback(
            source="trefle",
            names=seed_aliases,
            query_fn=self.trefle.fetch_optional_traits,
            trace_busca=trace_busca,
            disabled=not include_trefle,
        )
        responses["wikipedia"] = self.wikipedia.enrich_target_fields(
            scientific_valid=validated_name,
            scientific_suggested=ponto.nome_cientifico_sugerido,
            popular_name=ponto.nome_popular or (ponto.planta.nome_popular if ponto.planta else ""),
        )

        for key in ("gbif", "inaturalist", "trefle", "wikipedia"):
            if responses[key].get("error"):
                failures[key] = responses[key]["error"]

        attempted_integrations = ["global_names", "tropicos", "gbif", "inaturalist", "trefle", "wikipedia"]
        empty_integrations = [
            key for key in attempted_integrations
            if responses.get(key, {}).get("error") in {"not_found", "disabled", "missing_api_key"}
        ]
        failed_integrations = [
            key for key in attempted_integrations
            if responses.get(key, {}).get("error") and key not in empty_integrations
        ]

        consolidated = consolidar_resultados(
            scientific_name=scientific_name,
            gnv=responses["global_names"],
            tropicos=responses["tropicos"],
            gbif=responses["gbif"],
            inat=responses["inaturalist"],
            trefle=responses["trefle"],
            wikipedia=responses["wikipedia"],
        )
        consolidated["nomes_populares"] = dedupe_names(
            [ponto.nome_popular or "", (ponto.planta.nome_popular if ponto.planta else "") or ""]
        )
        consolidated["aliases_utilizados"] = seed_aliases

        success_count = sum(1 for key in ("global_names", "tropicos", "gbif", "inaturalist", "trefle", "wikipedia") if responses[key].get("ok"))
        failure_count = sum(1 for key in ("global_names", "tropicos", "gbif", "inaturalist", "trefle", "wikipedia") if responses[key].get("error"))
        consolidated["status_enriquecimento"] = status = definir_status_enriquecimento(success_count, failure_count, has_scientific_name=bool(scientific_name))

        divergencias: list[dict[str, Any]] = []
        local_confirmed = {
            "comestibilidade_status": bool(ponto.comestibilidade_confirmada),
            "parte_comestivel": bool(ponto.parte_comestivel_confirmada),
            "frutificacao_meses": bool(ponto.frutificacao_confirmada),
            "colheita_periodo": bool(ponto.colheita_confirmada),
        }
        local_values = {
            "comestibilidade_status": ponto.comestibilidade_status,
            "parte_comestivel": ponto.parte_comestivel_lista,
            "frutificacao_meses": ponto.frutificacao_meses,
            "colheita_periodo": ponto.colheita_periodo,
        }
        consolidated_values = {
            "comestibilidade_status": consolidated.get("comestibilidade_status"),
            "parte_comestivel": consolidated.get("parte_comestivel"),
            "frutificacao_meses": consolidated.get("frutificacao_meses"),
            "colheita_periodo": consolidated.get("colheita_periodo"),
        }
        for field_name, confirmed in local_confirmed.items():
            if not confirmed:
                continue
            local_value = local_values.get(field_name)
            new_value = consolidated_values.get(field_name)
            if local_value != new_value:
                divergencias.append(
                    {
                        "campo": field_name,
                        "valor_local": local_value,
                        "valor_enriquecimento": new_value,
                        "origem": (responses.get("wikipedia") or {}).get("source", {}).get("fonte", "pipeline"),
                    }
                )
            consolidated[field_name] = local_value
            if field_name == "comestibilidade_status":
                consolidated["comestibilidade_confirmada"] = True
            elif field_name == "parte_comestivel":
                consolidated["parte_comestivel_confirmada"] = True
            elif field_name == "frutificacao_meses":
                consolidated["frutificacao_confirmada"] = True
            elif field_name == "colheita_periodo":
                consolidated["colheita_confirmada"] = True

        grau = calcular_grau_confianca_taxonomica(
            gnv_ok=responses["global_names"].get("ok", False),
            tropicos_ok=responses["tropicos"].get("ok", False),
            gbif_ok=responses["gbif"].get("ok", False),
            inat_ok=responses["inaturalist"].get("ok", False),
            conflito_taxonomico=consolidated.get("conflito_taxonomico", False),
        )
        fontes_ok = [k for k in ("global_names", "tropicos", "gbif", "inaturalist", "trefle", "wikipedia") if responses.get(k, {}).get("ok")]

        ponto.nome_cientifico_submetido = consolidated["nome_cientifico_submetido"]
        ponto.nome_cientifico_validado = consolidated["nome_cientifico_validado"]
        ponto.nome_aceito = consolidated["nome_aceito"]
        ponto.autoria = consolidated["autoria"]
        ponto.sinonimos = consolidated["sinonimos"]
        ponto.fonte_taxonomica_primaria = consolidated["fonte_taxonomica_primaria"]
        ponto.fontes_taxonomicas_secundarias = consolidated["fontes_taxonomicas_secundarias"]
        ponto.grau_confianca_taxonomica = grau
        ponto.distribuicao_resumida = consolidated["distribuicao_resumida"]
        ponto.ocorrencias_gbif = consolidated["ocorrencias_gbif"]
        ponto.ocorrencias_inaturalist = consolidated["ocorrencias_inaturalist"]
        ponto.fenologia_observada = consolidated["fenologia_observada"]
        ponto.imagem_url = consolidated["imagem_url"]
        ponto.imagem_fonte = consolidated["imagem_fonte"]
        ponto.licenca_imagem = consolidated["licenca_imagem"]
        ponto.status_enriquecimento = status
        ponto.validacao_pendente_revisao_humana = bool(consolidated.get("conflito_taxonomico")) or grau < 0.65 or ambiguity.get("ambiguous", False)
        ponto.ultima_validacao_em = timezone.now()
        ponto.comestibilidade_status = consolidated.get("comestibilidade_status", "indeterminado")
        ponto.comestibilidade_confirmada = consolidated.get("comestibilidade_confirmada", False)
        ponto.parte_comestivel_lista = consolidated.get("parte_comestivel")
        ponto.parte_comestivel_confirmada = consolidated.get("parte_comestivel_confirmada", False)
        ponto.frutificacao_meses = consolidated.get("frutificacao_meses")
        ponto.frutificacao_confirmada = consolidated.get("frutificacao_confirmada", False)
        ponto.colheita_periodo = consolidated.get("colheita_periodo")
        ponto.colheita_confirmada = consolidated.get("colheita_confirmada", False)
        ponto.fontes_campos_enriquecimento = consolidated.get("fontes_campos_enriquecimento", {})
        ponto.integracoes_utilizadas = fontes_ok
        ponto.integracoes_com_falha = list(failures.keys())
        ponto.payload_resumido_validacao = {
            "origem": origem,
            "fontes_ok": fontes_ok,
            "fontes_falharam": failures,
            "integracoes_tentadas": attempted_integrations,
            "integracoes_retorno_vazio": empty_integrations,
            "integracoes_com_falha": failed_integrations,
            "campos_status_validacao": consolidated.get("status_validacao_campos", {}),
            "campos_fontes": consolidated.get("fontes_campos_enriquecimento", {}),
            "conflito_taxonomico": consolidated.get("conflito_taxonomico", False),
            "ambiguidade_taxonomica": ambiguity,
            "trace_busca": trace_busca,
            "dados_auxiliares_trefle": consolidated.get("dados_auxiliares_trefle", {}),
            "wikipedia": {
                "status": responses.get("wikipedia", {}).get("status"),
                "source": responses.get("wikipedia", {}).get("source"),
                "attempts": responses.get("wikipedia", {}).get("attempts", [])[:5],
                "error_type": responses.get("wikipedia", {}).get("error_type"),
            },
            "divergencias_campos_locais": divergencias,
        }
        ponto.fontes_enriquecimento = fontes_ok
        ponto.payload_enriquecimento = {"responses": {k: {kk: vv for kk, vv in v.items() if kk != "raw"} for k, v in responses.items()}}
        ponto.enriquecimento_atualizado_em = timezone.now()
        logger.info(
            "Persistindo enriquecimento ponto=%s status=%s fontes_ok=%s falhas=%s",
            ponto.id,
            status,
            fontes_ok,
            list(failures.keys()),
        )
        ponto.save()
        logger.info("Enriquecimento persistido ponto=%s atualizado_em=%s", ponto.id, ponto.enriquecimento_atualizado_em)

        if ponto.planta_id:
            planta = ponto.planta
            updated_fields = []
            if ponto.comestibilidade_confirmada:
                planta.comestivel = True if ponto.comestibilidade_status == "sim" else (False if ponto.comestibilidade_status == "nao" else None)
                updated_fields.append("comestivel")
            if ponto.parte_comestivel_confirmada and ponto.parte_comestivel_lista:
                planta.parte_comestivel = ", ".join(ponto.parte_comestivel_lista)
                updated_fields.append("parte_comestivel")
            if ponto.frutificacao_confirmada and ponto.frutificacao_meses:
                planta.epoca_frutificacao = ", ".join(ponto.frutificacao_meses)
                updated_fields.append("epoca_frutificacao")
            if ponto.colheita_confirmada and ponto.colheita_periodo:
                if isinstance(ponto.colheita_periodo, list):
                    planta.epoca_colheita = ", ".join(ponto.colheita_periodo)
                else:
                    planta.epoca_colheita = str(ponto.colheita_periodo)
                updated_fields.append("epoca_colheita")
            if updated_fields:
                planta.save(update_fields=updated_fields)

            self.canonical_store.persist_from_enrichment(
                planta,
                consolidated,
                fontes_ok=fontes_ok,
                aliases=seed_aliases,
                confidence=grau,
            )

        EnriquecimentoTaxonomicoHistorico.objects.create(
            ponto=ponto,
            status=status,
            grau_confianca=grau,
            fontes=fontes_ok,
            payload_resumido=ponto.payload_resumido_validacao,
            executado_em=timezone.now(),
        )

        logger.info("Enriquecimento ponto=%s status=%s fontes_ok=%s falhas=%s", ponto.id, status, fontes_ok, list(failures.keys()))

        return {
            "ok": True,
            "status_enriquecimento": status,
            "fontes_ok": fontes_ok,
            "fontes_falharam": failures,
            "grau_confianca_taxonomica": grau,
            "validacao_pendente_revisao_humana": ponto.validacao_pendente_revisao_humana,
            "ambiguidade_taxonomica": ambiguity,
        }

    def _query_with_fallback(
        self,
        *,
        source: str,
        names: list[str],
        query_fn,
        trace_busca: dict[str, Any],
        disabled: bool = False,
    ) -> tuple[dict[str, Any], list[str]]:
        if disabled:
            return {"ok": False, "error": "disabled", "error_type": "disabled"}, []
        last_result: dict[str, Any] = {"ok": False, "error": "not_found", "error_type": "not_found"}
        discovered_aliases: list[str] = []
        for name in dedupe_names(names):
            result = query_fn(name)
            trace_busca["consultas"].append({"fonte": source, "nome": name, "ok": bool(result.get("ok")), "erro": result.get("error")})
            if result.get("nome_cientifico_validado"):
                discovered_aliases.append(result.get("nome_cientifico_validado"))
            if result.get("nome_aceito"):
                discovered_aliases.append(result.get("nome_aceito"))
            discovered_aliases.extend(result.get("sinonimos") or [])
            if result.get("ok"):
                trace_busca["aliases"] = dedupe_names((trace_busca.get("aliases") or []) + discovered_aliases + [name])
                return result, dedupe_names(discovered_aliases)
            last_result = result
        trace_busca["aliases"] = dedupe_names((trace_busca.get("aliases") or []) + discovered_aliases)
        return last_result, dedupe_names(discovered_aliases)

    def _seed_aliases(self, ponto: PontoPANC, scientific_name: str) -> list[str]:
        planta_aliases = []
        if ponto.planta_id:
            planta_aliases = (ponto.planta.aliases or []) + (ponto.planta.sinonimos or []) + (ponto.planta.nomes_populares or [])
        return build_progressive_search_terms(
            submitted_scientific=scientific_name,
            validated_scientific=ponto.nome_cientifico_validado or (ponto.planta.nome_cientifico_validado if ponto.planta_id else ""),
            accepted_name=ponto.nome_aceito or (ponto.planta.nome_aceito if ponto.planta_id else ""),
            canonical_name=ponto.nome_cientifico_sugerido or "",
            current_name=ponto.nome_cientifico_submetido or "",
            synonyms=ponto.sinonimos or [],
            popular_names=[ponto.nome_popular or "", (ponto.planta.nome_popular if ponto.planta_id else "") or ""],
            aliases=planta_aliases,
        )

    def _hydrate_from_canonical(self, ponto: PontoPANC) -> None:
        planta = ponto.planta
        ponto.nome_cientifico_submetido = ponto.nome_cientifico_submetido or planta.nome_cientifico_submetido
        ponto.nome_cientifico_validado = planta.nome_cientifico_validado or planta.nome_cientifico
        ponto.nome_aceito = planta.nome_aceito or planta.nome_cientifico
        ponto.sinonimos = planta.sinonimos or []
        ponto.autoria = planta.autoria
        ponto.status_enriquecimento = "completo"
        ponto.fontes_enriquecimento = dedupe_names((planta.fontes_utilizadas or []) + ["base_local"])
        ponto.integracoes_utilizadas = ["base_local"]
        ponto.grau_confianca_taxonomica = max(float(planta.nivel_confianca_enriquecimento or 0), 0.8)
        ponto.distribuicao_resumida = planta.distribuicao_resumida
        ponto.imagem_url = planta.imagem_url
        ponto.imagem_fonte = planta.imagem_fonte
        ponto.licenca_imagem = planta.licenca_imagem
        ponto.ultima_validacao_em = timezone.now()
        ponto.enriquecimento_atualizado_em = timezone.now()
        ponto.save()

    def _resolve_scientific_from_popular(self, ponto: PontoPANC) -> str:
        popular = (ponto.nome_popular or (ponto.planta.nome_popular if ponto.planta else "") or "").strip()
        if not popular:
            return ""
        try:
            from mapping.models import PlantaReferencial

            planta = PlantaReferencial.objects.filter(nome_popular__iexact=popular).exclude(nome_cientifico="").first()
            return (planta.nome_cientifico if planta else "") or ""
        except Exception:
            logger.debug("Falha ao resolver nome científico por fallback de nome popular", exc_info=True)
            return ""

    def _extract_taxonomic_ambiguity(self, gnv_payload: dict[str, Any]) -> dict[str, Any]:
        raw = gnv_payload.get("raw") if isinstance(gnv_payload, dict) else {}
        data = raw.get("data") if isinstance(raw, dict) else None
        if not isinstance(data, list):
            return {"ambiguous": False, "candidates": []}

        candidates: list[dict[str, str]] = []
        seen: set[str] = set()
        for item in data[:8]:
            best = item.get("bestResult") if isinstance(item, dict) else {}
            canonical = (best.get("canonicalName") or "").strip()
            current = (best.get("currentName") or canonical or "").strip()
            if not current:
                continue
            key = current.lower()
            if key in seen:
                continue
            seen.add(key)
            candidates.append(
                {
                    "nome_cientifico": current,
                    "nome_canonico": canonical,
                    "fonte": "global_names",
                }
            )
        return {"ambiguous": len(candidates) > 1, "candidates": candidates}
