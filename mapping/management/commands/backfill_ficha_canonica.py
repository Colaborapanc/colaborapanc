from django.core.management.base import BaseCommand

from mapping.models import PontoPANC
from mapping.services.enrichment.planta_enrichment_pipeline import PlantaEnrichmentPipeline


class Command(BaseCommand):
    help = "Backfill de ficha canônica: enriquece pontos incompletos e associa aliases locais."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=200)
        parser.add_argument("--force", action="store_true", default=False)

    def handle(self, *args, **options):
        limit = options["limit"]
        force = options["force"]
        pipeline = PlantaEnrichmentPipeline()

        qs = PontoPANC.objects.select_related("planta").order_by("id")
        if not force:
            qs = qs.filter(status_enriquecimento__in=["pendente", "parcial"]) | qs.filter(planta__is_fully_enriched=False)

        pontos = list(qs.distinct()[:limit])
        self.stdout.write(self.style.NOTICE(f"Processando {len(pontos)} pontos (force={force})"))

        ok_count = 0
        fail_count = 0
        for ponto in pontos:
            try:
                result = pipeline.run_for_ponto(ponto, include_trefle=True, origem="backfill")
                if result.get("ok"):
                    ok_count += 1
                else:
                    fail_count += 1
            except Exception as exc:
                fail_count += 1
                self.stderr.write(f"Falha no ponto {ponto.id}: {exc}")

        self.stdout.write(self.style.SUCCESS(f"Backfill concluído: ok={ok_count} falhas={fail_count}"))
