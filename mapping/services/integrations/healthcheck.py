from __future__ import annotations

import os
import time
import traceback
from dataclasses import dataclass
from typing import Callable
import requests

from django.conf import settings
from django.utils import timezone

from mapping.models import IntegracaoMonitoramento, IntegracaoMonitoramentoLog
from mapping.services.biodiversity.gbif import GBIFService
from mapping.services.biodiversity.inaturalist import INaturalistService
from mapping.services.taxonomy.global_names import GlobalNamesService
from mapping.services.taxonomy.tropicos import TropicosService
from mapping.services.traits.trefle import TrefleTraitsService
from mapping.services.weather.inmet import INMETService
from mapping.services.weather.open_meteo import OpenMeteoService
from mapping.services.environment.mapbiomas import MapBiomasService
from mapping.services.nasa_firms_service import NASAFirmsService
from mapping.services.external.wikimedia_client import WikimediaClient
from mapping.services.ia_identificacao.plantid_health import PlantIdHealthService
from mapping.services.integrations.status_utils import (
    is_timeout_error,
    is_auth_error,
    classify_error_type,
    friendly_message,
    latency_level,
)


@dataclass
class IntegrationProbe:
    nome: str
    tipo: str
    requires_token: bool
    endpoint: str
    required_envs: list[str]
    config_checker: Callable[[], bool]
    checker: Callable[[], dict]


class IntegrationHealthcheckService:
    def _is_configured_env(self, *env_names: str) -> bool:
        return any(self._is_configured_setting_or_env(name) for name in env_names)

    def _is_configured_setting_or_env(self, name: str) -> bool:
        env_value = (os.environ.get(name) or "").strip()
        if env_value:
            return True
        setting_value = getattr(settings, name, "")
        return bool(str(setting_value).strip())

    def _missing_envs(self, env_names: list[str]) -> list[str]:
        return [name for name in env_names if not self._is_configured_setting_or_env(name)]

    def _summarize_result(self, result: dict, status_detail: str, configured: bool, error_message: str) -> str:
        if not configured:
            return "Integração não configurada no ambiente."
        if status_detail == "online":
            return "Operacional."
        if status_detail == "parcial":
            return "Operação parcial: resposta incompleta ou degradada."
        if status_detail == "timeout":
            return "Timeout na comunicação."
        if status_detail == "auth_error":
            return "Falha de autenticação/configuração."
        if error_message:
            return str(error_message)[:220]
        return str(result.get("message") or result.get("detail") or "Sem detalhes adicionais.")[:220]


    def probes(self) -> list[IntegrationProbe]:
        gnv = GlobalNamesService()
        trop = TropicosService()
        gbif = GBIFService()
        inat = INaturalistService()
        trefle = TrefleTraitsService()
        inmet = INMETService()
        open_meteo = OpenMeteoService()
        mapbiomas = MapBiomasService()
        nasa_firms = NASAFirmsService()
        wikimedia = WikimediaClient()
        plantid = PlantIdHealthService()

        return [
            IntegrationProbe("Global Names Verifier", "Taxonomia", False, f"{gnv.client.config.base_url}/verifications", [], lambda: True, lambda: gnv.validate_name("Poa annua")),
            IntegrationProbe("Tropicos", "Taxonomia", True, f"{trop.client.config.base_url}/Name/Search", ["TROPICOS_API_KEY"], lambda: self._is_configured_env("TROPICOS_API_KEY"), lambda: trop.resolve("Poa annua")),
            IntegrationProbe("GBIF", "Biodiversidade", False, f"{gbif.client.config.base_url}/species/match", [], lambda: True, lambda: gbif.fetch("Poa annua")),
            IntegrationProbe("iNaturalist", "Biodiversidade", False, f"{inat.client.config.base_url}/observations", [], lambda: True, lambda: inat.fetch("Poa annua")),
            IntegrationProbe("Trefle", "Traços botânicos", True, f"{trefle.client.config.base_url}/plants/search", ["TREFLE_API_TOKEN", "TREFLE_TOKEN"], lambda: self._is_configured_env("TREFLE_API_TOKEN", "TREFLE_TOKEN"), lambda: trefle.fetch_optional_traits("Poa annua")),
            IntegrationProbe("INMET", "Clima", False, inmet.endpoint, [], lambda: True, inmet.healthcheck),
            IntegrationProbe("Open-Meteo", "Clima", False, open_meteo.base_url, [], lambda: True, open_meteo.healthcheck),
            IntegrationProbe("MapBiomas", "Ambiental", True, mapbiomas.base_url, ["MAPBIOMAS_EMAIL", "MAPBIOMAS_PASSWORD"], lambda: all(self._is_configured_env(name) for name in ("MAPBIOMAS_EMAIL", "MAPBIOMAS_PASSWORD")), mapbiomas.healthcheck),
            IntegrationProbe(
                "NASA FIRMS",
                "Ambiental",
                True,
                f"{nasa_firms.api_url}/<MAP_KEY>/{nasa_firms.source}/<bbox>/1",
                ["NASA_FIRMS_MAP_KEY"],
                lambda: self._is_configured_env("NASA_FIRMS_MAP_KEY"),
                nasa_firms.healthcheck,
            ),
            IntegrationProbe(
                "PlantNet",
                "Identificação IA",
                True,
                os.environ.get("PLANTNET_API_URL", "https://my-api.plantnet.org/v2/identify/all"),
                ["PLANTNET_API_KEY"],
                lambda: self._is_configured_env("PLANTNET_API_KEY"),
                lambda: {"ok": self._is_configured_env("PLANTNET_API_KEY"), "error": None if self._is_configured_env("PLANTNET_API_KEY") else "missing_api_key"},
            ),
            IntegrationProbe(
                "Plant.id",
                "Identificação IA",
                True,
                f"{plantid.base_url}/identify",
                ["PLANTID_API_KEY"],
                lambda: self._is_configured_env("PLANTID_API_KEY"),
                plantid.healthcheck,
            ),
            IntegrationProbe(
                "Wikimedia",
                "Enriquecimento",
                False,
                "https://pt.wikipedia.org/w/api.php",
                ["WIKIMEDIA_USER", "WIKIMEDIA_EMAIL"],
                lambda: all(self._is_configured_setting_or_env(name) for name in ("WIKIMEDIA_USER", "WIKIMEDIA_EMAIL")),
                lambda: (lambda _res: {"ok": not _res[1], "error": _res[1], "error_type": wikimedia.classify_error(_res[1])})(wikimedia.search_page_candidates(query="Poa annua", language="pt", limit=1)),
            ),
        ]

    def run(self, only_name: str | None = None) -> list[dict]:
        output = []
        for probe in self.probes():
            if only_name and probe.nome != only_name:
                continue

            configured = bool(probe.config_checker())
            missing_env = self._missing_envs(probe.required_envs)
            started = time.perf_counter()
            if not configured and probe.requires_token:
                result = {"ok": False, "error": "missing_api_key", "error_type": "credencial_ausente"}
            else:
                try:
                    result = probe.checker() or {}
                except requests.Timeout:
                    result = {"ok": False, "error": "timeout", "error_type": "timeout"}
                except Exception as exc:
                    result = {"ok": False, "error": str(exc), "error_type": "erro_inesperado", "traceback": traceback.format_exc(limit=3)}
            elapsed = int((time.perf_counter() - started) * 1000)
            elapsed = int(result.get("latency_ms") or elapsed)

            ok = bool(result.get("ok")) and not result.get("error")
            status_code = result.get("status_code")
            has_http_failure = isinstance(status_code, int) and status_code >= 400
            summary_text = str(result.get("response_summary") or "").lower()
            has_http_error_summary = "http_error" in summary_text
            if has_http_failure or has_http_error_summary:
                ok = False
            if ok and result.get("error_type") in {"schema_error", "response_empty", "parse_error"}:
                ok = False
            explicit_error_type = result.get("error_type")
            error_message = result.get("error")
            if not explicit_error_type and "circuit_open" in str(error_message):
                explicit_error_type = "service_unavailable"
            if explicit_error_type == "rate_limited":
                explicit_error_type = "rate_limit"
            elif explicit_error_type == "network_error":
                explicit_error_type = "connection_error"
            elif explicit_error_type == "external_error":
                explicit_error_type = "endpoint_error"
            elif explicit_error_type == "servico_indisponivel":
                explicit_error_type = "service_unavailable"
            elif explicit_error_type == "resposta_vazia":
                explicit_error_type = "response_empty"

            plantid_nominal_online = (
                probe.nome == "Plant.id"
                and configured
                and explicit_error_type == "verificacao_limitada"
            )

            if plantid_nominal_online:
                ok = True
                degraded = False
                status = "online"
                status_detail = "online"
                error_message = None
                explicit_error_type = None
            else:
                degraded = explicit_error_type == "verificacao_limitada" or (bool(result.get("ok")) and bool(result.get("error")))
                status = "online" if ok else ("degradada" if degraded else "offline")

            if plantid_nominal_online:
                status_detail = "online"
            elif not configured and probe.requires_token:
                status_detail = "nao_configurada"
            elif ok and not error_message:
                status_detail = "online"
            elif explicit_error_type == "verificacao_limitada":
                status_detail = "verificacao_limitada"
            elif degraded:
                status_detail = "parcial"
            elif explicit_error_type in {"auth_error", "forbidden", "not_found", "rate_limit", "connection_error", "parse_error", "endpoint_error", "schema_error", "service_unavailable", "configuracao_invalida", "response_empty", "http_error"}:
                status_detail = explicit_error_type
            elif is_timeout_error(error_message):
                status_detail = "timeout"
            elif is_auth_error(error_message):
                status_detail = "auth_error"
            else:
                status_detail = "offline"

            obj, _ = IntegracaoMonitoramento.objects.get_or_create(
                nome=probe.nome,
                defaults={"requer_chave": probe.requires_token, "endpoint_healthcheck": probe.endpoint},
            )
            obj.status = status
            obj.tempo_resposta_ms = elapsed
            obj.requer_chave = probe.requires_token
            obj.endpoint_healthcheck = result.get("endpoint") or probe.endpoint
            obj.ultimo_erro = error_message or ""
            if status == "online":
                obj.ultimo_teste_bem_sucedido = timezone.now()
            obj.save()

            IntegracaoMonitoramentoLog.objects.create(
                integracao=obj,
                status=status,
                detalhe=str(
                    {
                        "integration": probe.nome,
                        "endpoint": result.get("endpoint") or probe.endpoint,
                        "method": result.get("method", "GET"),
                        "status_code": result.get("status_code"),
                        "latency_ms": elapsed,
                        "error_type": explicit_error_type or status_detail,
                        "message": error_message or "ok",
                        "missing_env": missing_env,
                        "query_params": result.get("query_params"),
                        "request_headers": result.get("request_headers"),
                        "response_summary": result.get("result_summary") or result.get("response_summary"),
                        "response_excerpt": result.get("response_excerpt"),
                        "traceback": result.get("traceback"),
                    }
                )[:1800],
                tempo_resposta_ms=elapsed,
            )

            logs_recentes = list(obj.logs.values("status", "detalhe", "tempo_resposta_ms", "criado_em")[:5])
            ultima_falha = next(
                (
                    log for log in logs_recentes
                    if log.get("status") != "online"
                ),
                None,
            )
            error_type = classify_error_type(status_detail, error_message or "", configured)

            output.append(
                {
                    "nome": probe.nome,
                    "tipo_integracao": probe.tipo,
                    "status": status,
                    "status_detalhado": status_detail,
                    "sucesso": status == "online",
                    "configurada": configured,
                    "operacional": status == "online",
                    "ultima_verificacao": obj.atualizado_em,
                    "ultimo_teste_bem_sucedido": obj.ultimo_teste_bem_sucedido,
                    "ultimo_erro": obj.ultimo_erro,
                    "tempo_resposta_ms": elapsed,
                    "requer_chave": probe.requires_token,
                    "quota_limite": obj.quota_limite,
                    "endpoint_healthcheck": result.get("endpoint") or probe.endpoint,
                    "atualizado_em": obj.atualizado_em,
                    "resposta_resumida": self._summarize_result(result, status_detail, configured, error_message),
                    "error_type": error_type,
                    "env_vars_ausentes": missing_env,
                    "variaveis_esperadas": probe.required_envs,
                    "mensagem_tecnica": (error_message or "ok")[:240],
                    "mensagem_amigavel": friendly_message(
                        status_detail,
                        configured,
                        error_type,
                    ),
                    "ultima_falha_em": ultima_falha.get("criado_em") if ultima_falha else None,
                    "ultimo_tipo_problema": error_type if error_type != "nenhum" else "-",
                    "latencia_nivel": latency_level(elapsed),
                    "logs_recentes": logs_recentes,
                }
            )
        return output
