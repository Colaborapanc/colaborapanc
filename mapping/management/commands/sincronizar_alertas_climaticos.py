from django.core.management.base import BaseCommand

from mapping.services.climate_alert_service import ClimateAlertService


class Command(BaseCommand):
    help = "Sincroniza alertas climáticos (INMET + Open-Meteo) por ponto"

    def add_arguments(self, parser):
        parser.add_argument("--ponto-id", type=int, help="ID do ponto a sincronizar")
        parser.add_argument("--only-active", action="store_true", help="Persistir somente alertas ativos")

    def handle(self, *args, **options):
        service = ClimateAlertService()
        result = service.sync(
            ponto_id=options.get("ponto_id"),
            only_active=options.get("only_active", False),
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"Sincronização concluída: criados={result.created} atualizados={result.updated} ignorados={result.skipped} erros={result.errors}"
            )
        )
