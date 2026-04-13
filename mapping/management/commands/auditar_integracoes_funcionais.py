from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from django.core.management.base import BaseCommand

from mapping.models import IntegracaoMonitoramento


@dataclass
class IntegrationAudit:
    nome: str
    aliases: tuple[str, ...]
    backend_markers: tuple[str, ...]
    serializer_markers: tuple[str, ...]
    mobile_markers: tuple[str, ...]


class Command(BaseCommand):
    help = "Audita evidências funcionais de integrações (healthcheck + uso + exposição + consumo)."

    AUDITS = (
        IntegrationAudit(
            nome="PlantNet",
            aliases=("plantnet", "plant net"),
            backend_markers=("identificar_plantnet", "PlantNetProvider", "plantnet"),
            serializer_markers=("score_identificacao", "nome_cientifico_sugerido"),
            mobile_markers=("identificarPlanta", "identificacaoService"),
        ),
        IntegrationAudit(
            nome="Plant.id",
            aliases=("plantid", "plant.id"),
            backend_markers=("identificar_plantid", "PlantIdProvider", "plantid"),
            serializer_markers=("score_identificacao", "nome_cientifico_sugerido"),
            mobile_markers=("identificarPlanta", "identificacaoService"),
        ),
        IntegrationAudit(
            nome="Global Names Verifier",
            aliases=("global names", "gnv"),
            backend_markers=("GlobalNames", "global_names"),
            serializer_markers=("nome_cientifico_validado", "fonte_taxonomica_primaria"),
            mobile_markers=("nome_cientifico_validado",),
        ),
        IntegrationAudit(
            nome="Tropicos",
            aliases=("tropicos",),
            backend_markers=("Tropicos", "tropicos"),
            serializer_markers=("nome_aceito", "sinonimos"),
            mobile_markers=("nome_aceito", "sinonimos"),
        ),
        IntegrationAudit(
            nome="Trefle",
            aliases=("trefle",),
            backend_markers=("Trefle", "trefle"),
            serializer_markers=("comestibilidade_status", "parte_comestivel_lista"),
            mobile_markers=("comestibilidade_status", "parte_comestivel"),
        ),
        IntegrationAudit(
            nome="GBIF",
            aliases=("gbif",),
            backend_markers=("GBIF", "ocorrencias_gbif"),
            serializer_markers=("ocorrencias_gbif",),
            mobile_markers=("ocorrencias_gbif",),
        ),
        IntegrationAudit(
            nome="iNaturalist",
            aliases=("inaturalist",),
            backend_markers=("INaturalist", "ocorrencias_inaturalist"),
            serializer_markers=("ocorrencias_inaturalist", "fenologia_observada"),
            mobile_markers=("ocorrencias_inaturalist", "fenologia_observada"),
        ),
        IntegrationAudit(
            nome="Wikimedia",
            aliases=("wikimedia", "wikipedia"),
            backend_markers=("WikipediaEnrichmentService", "wikipedia"),
            serializer_markers=("payload_resumido_validacao",),
            mobile_markers=("enriquecimento",),
        ),
        IntegrationAudit(
            nome="MapBiomas",
            aliases=("mapbiomas",),
            backend_markers=("MapBiomas", "environmental"),
            serializer_markers=("alertas",),
            mobile_markers=("alertas",),
        ),
        IntegrationAudit(
            nome="INMET",
            aliases=("inmet",),
            backend_markers=("INMET", "weather"),
            serializer_markers=("alertas",),
            mobile_markers=("alertas",),
        ),
        IntegrationAudit(
            nome="Open-Meteo",
            aliases=("open-meteo", "open_meteo"),
            backend_markers=("OpenMeteo", "open_meteo"),
            serializer_markers=("alertas",),
            mobile_markers=("alertas",),
        ),
    )

    def handle(self, *args, **options):
        repo_root = Path(__file__).resolve().parents[4]
        backend_paths = [
            repo_root / "mapping" / "services",
            repo_root / "mapping" / "views.py",
            repo_root / "mapping" / "signals.py",
        ]
        serializer_paths = [repo_root / "mapping" / "serializers.py", repo_root / "mapping" / "views_enrichment.py"]
        mobile_paths = [repo_root / "mobile" / "src" / "services", repo_root / "mobile" / "src" / "screens"]

        backend_blob = self._collect_text(backend_paths)
        serializer_blob = self._collect_text(serializer_paths)
        mobile_blob = self._collect_text(mobile_paths)

        self.stdout.write("=== AUDITORIA FUNCIONAL DE INTEGRAÇÕES ===")

        for audit in self.AUDITS:
            status_health = self._health_status(audit)
            backend_ok = self._contains_any(backend_blob, audit.backend_markers + audit.aliases)
            serializer_ok = self._contains_any(serializer_blob, audit.serializer_markers + audit.aliases)
            mobile_ok = self._contains_any(mobile_blob, audit.mobile_markers + audit.aliases)

            if status_health == "online" and all([backend_ok, serializer_ok, mobile_ok]):
                final_status = "integração plenamente operacional no produto"
            elif status_health == "online":
                final_status = "healthcheck ok, mas sem efeito funcional completo"
            else:
                final_status = "healthcheck não está online"

            self.stdout.write(
                f"- {audit.nome}: health={status_health} | chamada_funcional={backend_ok} | "
                f"exposicao_api={serializer_ok} | consumo_mobile={mobile_ok} | status_final={final_status}"
            )

    def _collect_text(self, paths: list[Path]) -> str:
        chunks: list[str] = []
        for p in paths:
            if not p.exists():
                continue
            if p.is_file() and p.suffix in {".py", ".js", ".ts", ".tsx"}:
                chunks.append(self._safe_read(p))
            elif p.is_dir():
                for child in p.rglob("*"):
                    if child.suffix in {".py", ".js", ".ts", ".tsx"} and child.is_file():
                        chunks.append(self._safe_read(child))
        return "\n".join(chunks).lower()

    def _safe_read(self, path: Path) -> str:
        try:
            return path.read_text(encoding="utf-8")
        except Exception:
            return ""

    def _contains_any(self, blob: str, terms: tuple[str, ...]) -> bool:
        return any(term.lower() in blob for term in terms if term)

    def _health_status(self, audit: IntegrationAudit) -> str:
        monitors = IntegracaoMonitoramento.objects.filter(nome__iexact=audit.nome)
        if monitors.exists():
            return monitors.order_by("-atualizado_em").first().status

        for alias in audit.aliases:
            monitor = IntegracaoMonitoramento.objects.filter(nome__icontains=alias).order_by("-atualizado_em").first()
            if monitor:
                return monitor.status

        return "desconhecido"
