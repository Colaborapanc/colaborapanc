import os
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.conf import settings
from mapping.models import PontoPANC

class Command(BaseCommand):
    help = 'Remove fotos de identificação temporárias (usadas apenas para identificação automática)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dias',
            type=int,
            default=7,
            help='Remove imagens com mais de N dias (padrão: 7 dias)'
        )
        parser.add_argument(
            '--aprovados',
            action='store_true',
            help='Remove também as fotos de pontos já aprovados/moderados'
        )

    def handle(self, *args, **options):
        dias = options['dias']
        remove_aprovados = options['aprovados']

        limite = datetime.now() - timedelta(days=dias)
        qs = PontoPANC.objects.filter(criado_em__lt=limite)

        if not remove_aprovados:
            qs = qs.exclude(status='aprovado')

        count = 0
        for ponto in qs:
            if ponto.foto_identificacao and os.path.isfile(ponto.foto_identificacao.path):
                try:
                    os.remove(ponto.foto_identificacao.path)
                    self.stdout.write(f"Removido: {ponto.foto_identificacao.path}")
                    ponto.foto_identificacao = None
                    ponto.save()
                    count += 1
                except Exception as e:
                    self.stderr.write(f"Erro ao remover {ponto.foto_identificacao.path}: {e}")

        self.stdout.write(self.style.SUCCESS(f"Total de imagens removidas: {count}"))
# python manage.py limpar_fotos_identificacao --dias 2 
# 0 3 * * 1 /caminho/para/seu/venv/bin/python /caminho/para/seu/manage.py limpar_fotos_identificacao