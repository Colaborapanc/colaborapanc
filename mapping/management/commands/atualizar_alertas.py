from django.core.management.base import BaseCommand
from mapping.services.alertas_api import atualizar_alertas_rss
from mapping.services.alertas_openmeteo import atualizar_alertas_openmeteo
from mapping.services.environmental_monitor_service import EnvironmentalMonitorService

class Command(BaseCommand):
    help = 'Atualiza os alertas climáticos via fontes externas'

    def handle(self, *args, **kwargs):
        self.stdout.write("[🌦️] Iniciando atualização automática de alertas...")
        atualizar_alertas_rss()
        atualizar_alertas_openmeteo()
        monitor_service = EnvironmentalMonitorService()
        resultado = monitor_service.sync()
        self.stdout.write(
            f"[🌎] Alertas ambientais: criados={resultado.created} atualizados={resultado.updated} erros={resultado.errors}"
        )
        self.stdout.write("[✅] Atualização concluída.")
