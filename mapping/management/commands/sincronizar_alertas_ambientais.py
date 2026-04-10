from django.core.management.base import BaseCommand
import time

from mapping.services.environmental_monitor_service import EnvironmentalMonitorService


class Command(BaseCommand):
    help = "Sincroniza alertas ambientais (MapBiomas e NASA FIRMS) por ponto"

    def add_arguments(self, parser):
        parser.add_argument("--ponto-id", type=int, help="ID do ponto a sincronizar")
        parser.add_argument("--fonte", choices=["mapbiomas", "nasa_firms"], help="Fonte específica")
        parser.add_argument("--days", type=int, help="Janela de dias para sincronização incremental")
        parser.add_argument("--raio", type=int, help="Raio em metros para busca")
        parser.add_argument("--full", action="store_true", help="Reprocessamento completo")
        parser.add_argument(
            "--latest-only",
            action="store_true",
            help="Sincroniza apenas o evento mais recente de cada fonte por ponto",
        )
        parser.add_argument(
            "--loop",
            action="store_true",
            help="Executa sincronização contínua em intervalo fixo (padrão: 30 min)",
        )
        parser.add_argument(
            "--interval-minutes",
            type=int,
            default=30,
            help="Intervalo em minutos quando usar --loop (padrão: 30)",
        )

    def handle(self, *args, **options):
        interval_seconds = max(1, options.get("interval_minutes") * 60)
        executar_loop = options.get("loop", False)

        while True:
            self.stdout.write("[🌎] Iniciando sincronização de alertas ambientais...")
            service = EnvironmentalMonitorService()
            result = service.sync(
                ponto_id=options.get("ponto_id"),
                fonte=options.get("fonte"),
                days=options.get("days"),
                raio=options.get("raio"),
                full=options.get("full", False),
                latest_only=options.get("latest_only", False),
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f"[✅] Concluído: criados={result.created} atualizados={result.updated} erros={result.errors}"
                )
            )
            if not executar_loop:
                break

            self.stdout.write(
                f"[⏱️] Aguardando {options.get('interval_minutes')} minutos para próxima sincronização..."
            )
            time.sleep(interval_seconds)
