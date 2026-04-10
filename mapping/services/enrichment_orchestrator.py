"""
Orquestrador de enriquecimento taxonômico.

Pipeline:
1. Receber nome científico digitado no cadastro.
2. Validar no Global Names Verifier.
3. Com o nome validado, consultar Tropicos (nome aceito, sinonímia, autoria, imagens).
4. Consultar GBIF (ocorrências, mapas, imagens).
5. Consultar iNaturalist (observações, fenologia).
6. Cruzar resultados e gerar grau de confiança.
7. Conflitos: Global Names + Tropicos para taxonomia; GBIF + iNaturalist para ocorrência/fenologia.
8. Trefle apenas sugere extras (comestibilidade) - nunca confirma sozinho.
9. Nunca usar Wikipedia.
10. Se alguma API falhar, salvar mesmo assim como enriquecimento parcial.
"""

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

import requests
from django.utils import timezone
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from mapping.models import HistoricoEnriquecimento, PlantaReferencial

logger = logging.getLogger(__name__)


def _build_session() -> requests.Session:
    retry_kwargs = {
        "total": 2,
        "read": 2,
        "connect": 2,
        "status_forcelist": [429, 500, 502, 503, 504],
        "backoff_factor": 0.3,
    }
    try:
        retry = Retry(allowed_methods=["GET", "POST"], **retry_kwargs)
    except TypeError:
        retry = Retry(method_whitelist=["GET", "POST"], **retry_kwargs)
    adapter = HTTPAdapter(max_retries=retry)
    session = requests.Session()
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


class EnrichmentOrchestrator:
    def __init__(self):
        self.session = _build_session()

    def enrich(self, nome_cientifico: str, planta: PlantaReferencial | None = None, usuario=None) -> dict:
        """
        Executa o pipeline completo de enriquecimento.
        Retorna dict com todos os dados consolidados + status.
        Se planta for fornecida, atualiza os campos diretamente.
        """
        nome_cientifico = (nome_cientifico or "").strip()
        if not nome_cientifico:
            return {"sucesso": False, "erro": "Nome científico não informado", "status": "erro"}

        erros = []
        fontes_consultadas = []

        # ---- Etapa 1: Global Names Verifier ----
        gn_result = self._call_global_names(nome_cientifico)
        fontes_consultadas.append("Global Names Verifier")

        # Determinar nome validado para consultas subsequentes
        nome_validado = nome_cientifico
        if gn_result.get("sucesso") and gn_result.get("nome_validado"):
            nome_validado = gn_result["nome_validado"]
        elif not gn_result.get("sucesso"):
            erros.append(f"Global Names: {gn_result.get('erro', 'erro desconhecido')}")

        # ---- Etapas 2-5: Consultas paralelas com o nome validado ----
        tropicos_result = {}
        gbif_result = {}
        inat_result = {}
        trefle_result = {}

        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {
                executor.submit(self._call_tropicos, nome_validado): "tropicos",
                executor.submit(self._call_gbif, nome_validado): "gbif",
                executor.submit(self._call_inaturalist, nome_validado): "inaturalist",
                executor.submit(self._call_trefle, nome_validado): "trefle",
            }
            for future in as_completed(futures):
                source = futures[future]
                try:
                    result = future.result()
                    if source == "tropicos":
                        tropicos_result = result
                        fontes_consultadas.append("Tropicos")
                    elif source == "gbif":
                        gbif_result = result
                        fontes_consultadas.append("GBIF")
                    elif source == "inaturalist":
                        inat_result = result
                        fontes_consultadas.append("iNaturalist")
                    elif source == "trefle":
                        trefle_result = result
                        fontes_consultadas.append("Trefle")

                    if not result.get("sucesso"):
                        erros.append(f"{source}: {result.get('erro', 'erro desconhecido')}")
                except Exception as exc:
                    erros.append(f"{source}: {exc}")
                    logger.exception("Erro no enriquecimento %s", source)

        # ---- Etapa 6: Cruzar resultados e gerar grau de confiança ----
        consolidated = self._consolidate(
            nome_cientifico=nome_cientifico,
            nome_validado=nome_validado,
            gn=gn_result,
            tropicos=tropicos_result,
            gbif=gbif_result,
            inat=inat_result,
            trefle=trefle_result,
        )

        # Determinar status
        fontes_com_sucesso = sum(1 for r in [gn_result, tropicos_result, gbif_result, inat_result] if r.get("sucesso"))
        if fontes_com_sucesso == 4:
            status = "completo"
        elif fontes_com_sucesso >= 1:
            status = "parcial"
        else:
            status = "erro"

        consolidated["status"] = status
        consolidated["erros"] = erros
        consolidated["fontes_consultadas"] = fontes_consultadas

        # ---- Persistir no modelo se planta fornecida ----
        if planta:
            self._apply_to_planta(planta, consolidated)

        # ---- Salvar histórico ----
        if planta:
            try:
                HistoricoEnriquecimento.objects.create(
                    planta=planta,
                    fontes_consultadas=fontes_consultadas,
                    resultado=consolidated,
                    status=status,
                    erro_detalhes="\n".join(erros) if erros else None,
                    usuario=usuario,
                )
            except Exception as exc:
                logger.exception("Falha ao salvar histórico de enriquecimento: %s", exc)

        return consolidated

    def _call_global_names(self, nome: str) -> dict:
        from mapping.services.globalnames_service import GlobalNamesService
        return GlobalNamesService(session=self.session).verify(nome)

    def _call_tropicos(self, nome: str) -> dict:
        from mapping.services.tropicos_service import TropicosService
        return TropicosService(session=self.session).search_name(nome)

    def _call_gbif(self, nome: str) -> dict:
        from mapping.services.gbif_enrichment_service import GBIFEnrichmentService
        return GBIFEnrichmentService(session=self.session).enrich(nome)

    def _call_inaturalist(self, nome: str) -> dict:
        from mapping.services.inaturalist_enrichment_service import INaturalistEnrichmentService
        return INaturalistEnrichmentService(session=self.session).enrich(nome)

    def _call_trefle(self, nome: str) -> dict:
        from mapping.services.trefle_service import TrefleService
        return TrefleService(session=self.session).enrich(nome)

    def _consolidate(self, *, nome_cientifico: str, nome_validado: str,
                     gn: dict, tropicos: dict, gbif: dict, inat: dict, trefle: dict) -> dict:
        """
        Regras de cruzamento:
        - Taxonomia: priorizar Global Names + Tropicos
        - Ocorrências/fenologia: priorizar GBIF + iNaturalist
        - Trefle: apenas sugestão de extras
        """

        # --- Nome aceito ---
        # Prioridade: Tropicos > Global Names > GBIF
        nome_aceito = ""
        if tropicos.get("sucesso") and tropicos.get("nome_aceito"):
            nome_aceito = tropicos["nome_aceito"]
        elif gn.get("sucesso") and gn.get("nome_validado"):
            nome_aceito = gn["nome_validado"]
        elif gbif.get("sucesso") and gbif.get("nome_aceito"):
            nome_aceito = gbif["nome_aceito"]

        # --- Autoria ---
        autoria = ""
        if tropicos.get("sucesso") and tropicos.get("autoria"):
            autoria = tropicos["autoria"]
        elif gn.get("sucesso") and gn.get("autoria"):
            autoria = gn["autoria"]
        elif gbif.get("sucesso") and gbif.get("autoria"):
            autoria = gbif["autoria"]

        # --- Sinônimos ---
        sinonimos_set: set[str] = set()
        if gn.get("sucesso"):
            for s in gn.get("sinonimos") or []:
                sinonimos_set.add(s)
        if tropicos.get("sucesso"):
            for s in tropicos.get("sinonimos") or []:
                nome_s = s.get("nome") if isinstance(s, dict) else s
                if nome_s:
                    sinonimos_set.add(nome_s)
        sinonimos = sorted(sinonimos_set)[:30]

        # --- Fonte taxonômica primária ---
        fonte_primaria = ""
        if tropicos.get("sucesso"):
            fonte_primaria = "Tropicos"
        elif gn.get("sucesso"):
            fonte_primaria = f"Global Names ({gn.get('data_source_title', '')})"

        fontes_secundarias = []
        if gbif.get("sucesso"):
            fontes_secundarias.append("GBIF")
        if inat.get("sucesso"):
            fontes_secundarias.append("iNaturalist")
        if trefle.get("sucesso"):
            fontes_secundarias.append("Trefle (sugestão)")

        # --- Distribuição ---
        distribuicao_partes = []
        if gbif.get("sucesso") and gbif.get("distribuicao_paises"):
            paises = gbif["distribuicao_paises"][:10]
            distribuicao_partes.append(f"GBIF: {', '.join(paises)}")
        if tropicos.get("sucesso") and tropicos.get("distribuicao"):
            distribuicao_partes.append(f"Tropicos: {tropicos['distribuicao']}")
        distribuicao_resumida = "; ".join(distribuicao_partes) if distribuicao_partes else ""

        # --- Ocorrências ---
        ocorrencias_gbif = gbif.get("ocorrencias_total", 0) if gbif.get("sucesso") else None
        ocorrencias_inat = inat.get("ocorrencias_total", 0) if inat.get("sucesso") else None

        # --- Fenologia (iNaturalist) ---
        fenologia = inat.get("fenologia") or {} if inat.get("sucesso") else {}

        # --- Imagem ---
        # Prioridade: iNaturalist (CC licensed) > GBIF > Tropicos > Trefle
        imagem_url = ""
        imagem_fonte = ""
        licenca_imagem = ""

        if inat.get("sucesso") and inat.get("imagens"):
            img = inat["imagens"][0]
            imagem_url = img.get("url", "")
            imagem_fonte = f"iNaturalist - {img.get('atribuicao', '')}"
            licenca_imagem = img.get("licenca", "")
        elif gbif.get("sucesso") and gbif.get("imagens"):
            img = gbif["imagens"][0]
            imagem_url = img.get("url", "")
            imagem_fonte = img.get("fonte", "GBIF")
            licenca_imagem = img.get("licenca", "")
        elif tropicos.get("sucesso") and tropicos.get("imagens"):
            img = tropicos["imagens"][0]
            imagem_url = img.get("url", "")
            imagem_fonte = f"Tropicos - {img.get('copyright', '')}"
            licenca_imagem = img.get("copyright", "")
        elif trefle.get("sucesso") and trefle.get("imagem_url"):
            imagem_url = trefle["imagem_url"]
            imagem_fonte = "Trefle (sugestão)"
            licenca_imagem = ""

        # --- Grau de confiança ---
        grau = self._compute_confidence(gn=gn, tropicos=tropicos, gbif=gbif, inat=inat, nome_validado=nome_validado, nome_cientifico=nome_cientifico)

        return {
            "nome_cientifico_submetido": nome_cientifico,
            "nome_cientifico_validado": nome_validado,
            "nome_aceito": nome_aceito,
            "sinonimos": sinonimos,
            "autoria": autoria,
            "fonte_taxonomica_primaria": fonte_primaria,
            "fontes_secundarias": fontes_secundarias,
            "grau_confianca": grau,
            "distribuicao_resumida": distribuicao_resumida,
            "ocorrencias_gbif": ocorrencias_gbif,
            "ocorrencias_inaturalist": ocorrencias_inat,
            "fenologia_observada": fenologia,
            "imagem_url": imagem_url,
            "imagem_fonte": imagem_fonte,
            "licenca_imagem": licenca_imagem,
            # Payload resumido das fontes
            "payload_resumido": {
                "global_names": {k: v for k, v in gn.items() if k != "raw"} if gn.get("sucesso") else {"erro": gn.get("erro")},
                "tropicos": {k: v for k, v in tropicos.items() if k != "raw"} if tropicos.get("sucesso") else {"erro": tropicos.get("erro")},
                "gbif": {k: v for k, v in gbif.items() if k != "raw"} if gbif.get("sucesso") else {"erro": gbif.get("erro")},
                "inaturalist": {k: v for k, v in inat.items() if k != "raw"} if inat.get("sucesso") else {"erro": inat.get("erro")},
                "trefle": {k: v for k, v in trefle.items() if k != "raw"} if trefle.get("sucesso") else {"erro": trefle.get("erro")},
            },
            # Extras do Trefle (sugestão apenas)
            "trefle_extras": {
                "comestivel": trefle.get("comestivel"),
                "partes_comestiveis": trefle.get("partes_comestiveis") or [],
            } if trefle.get("sucesso") else None,
        }

    def _compute_confidence(self, *, gn: dict, tropicos: dict, gbif: dict, inat: dict,
                            nome_validado: str, nome_cientifico: str) -> float:
        """
        Calcula grau de confiança (0.0 a 1.0) baseado em concordância das fontes.

        Pesos máximos (soma = 1.0):
        - Global Names: até 0.30
        - Tropicos:     até 0.25
        - GBIF:         até 0.20
        - iNaturalist:  até 0.15
        - Concordância: até 0.10
        """
        score = 0.0

        # Global Names match (peso 30%)
        if gn.get("sucesso"):
            gn_score = gn.get("score", 0.0)
            score += gn_score * 0.30

        # Tropicos (peso 25%)
        if tropicos.get("sucesso"):
            score += 0.20
            if tropicos.get("nome_aceito"):
                score += 0.05

        # GBIF (peso 20%)
        if gbif.get("sucesso"):
            match_type = (gbif.get("match_type") or "").upper()
            if match_type == "EXACT":
                score += 0.20
            elif match_type == "FUZZY":
                score += 0.12
            else:
                score += 0.05

        # iNaturalist (peso 15%)
        if inat.get("sucesso"):
            score += 0.15

        # Concordância entre fontes (peso 10%)
        nomes = set()
        if gn.get("sucesso") and gn.get("nome_validado"):
            nomes.add(gn["nome_validado"].lower().strip())
        if tropicos.get("sucesso") and tropicos.get("nome_aceito"):
            nomes.add(tropicos["nome_aceito"].lower().strip())
        if gbif.get("sucesso") and gbif.get("nome_aceito"):
            nomes.add(gbif["nome_aceito"].lower().strip())
        if len(nomes) == 1 and nomes:
            score += 0.10  # concordância total entre fontes

        return round(min(score, 1.0), 2)

    def _apply_to_planta(self, planta: PlantaReferencial, data: dict) -> None:
        """Aplica dados consolidados nos campos da PlantaReferencial."""
        fields_to_update = []

        field_map = {
            "nome_cientifico_submetido": "nome_cientifico_submetido",
            "nome_cientifico_validado": "nome_cientifico_validado",
            "nome_aceito": "nome_aceito",
            "sinonimos": "sinonimos",
            "autoria": "autoria",
            "fonte_taxonomica_primaria": "fonte_taxonomica_primaria",
            "fontes_secundarias": "fontes_secundarias",
            "grau_confianca": "grau_confianca",
            "distribuicao_resumida": "distribuicao_resumida",
            "ocorrencias_gbif": "ocorrencias_gbif",
            "ocorrencias_inaturalist": "ocorrencias_inaturalist",
            "fenologia_observada": "fenologia_observada",
            "imagem_url": "imagem_url",
            "imagem_fonte": "imagem_fonte",
            "licenca_imagem": "licenca_imagem",
        }

        for data_key, model_field in field_map.items():
            value = data.get(data_key)
            if value is not None and value != "":
                setattr(planta, model_field, value)
                fields_to_update.append(model_field)

        planta.status_enriquecimento = data.get("status", "parcial")
        fields_to_update.append("status_enriquecimento")

        planta.ultima_validacao_em = timezone.now()
        fields_to_update.append("ultima_validacao_em")

        planta.payload_enriquecimento = data.get("payload_resumido", {})
        fields_to_update.append("payload_enriquecimento")

        # Atualizar nome_cientifico_valido se temos nome aceito melhor
        if data.get("nome_aceito") and not planta.nome_cientifico_valido:
            planta.nome_cientifico_valido = data["nome_aceito"]
            fields_to_update.append("nome_cientifico_valido")

        if data.get("fonte_taxonomica_primaria") and not planta.fonte_validacao:
            planta.fonte_validacao = data["fonte_taxonomica_primaria"]
            fields_to_update.append("fonte_validacao")

        try:
            planta.save(update_fields=list(set(fields_to_update)))
        except Exception as exc:
            logger.exception("Falha ao salvar enriquecimento na planta %s: %s", planta.pk, exc)
