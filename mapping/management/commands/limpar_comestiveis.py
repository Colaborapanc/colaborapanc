import time
import logging
from django.core.management.base import BaseCommand
from mapping.models import PlantaReferencial
from mapping.utils import wikipedia
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm

logging.basicConfig(filename='log_exclusoes.txt', level=logging.INFO, format='%(asctime)s - %(message)s')

class Command(BaseCommand):
    help = 'Remove plantas não comestíveis da base usando Wikipedia com threads paralelas.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--workers',
            type=int,
            default=8,
            help='Número de threads paralelas para processar plantas (default: 8)'
        )

    def handle(self, *args, **options):
        inicio = time.time()
        workers = options['workers']
        total = PlantaReferencial.objects.count()
        self.stdout.write(self.style.WARNING(
            f"\nIniciando triagem de {total} plantas com {workers} threads...\n"
        ))

        plantas = list(PlantaReferencial.objects.all())
        progresso = tqdm(total=total, desc="Verificando", unit="planta")

        def verificar_e_excluir(planta):
            nome = planta.nome_cientifico.strip() or planta.nome_popular.strip()
            if not nome:
                progresso.update(1)
                return
            try:
                if not wikipedia.verificar_comestibilidade(nome):
                    PlantaReferencial.objects.filter(id=planta.id).delete()
                    logging.info(f"Removido: {nome} (ID {planta.id}) - Não comestível")
            except Exception as e:
                logging.warning(f"Erro ao processar {nome} (ID {planta.id}): {e}")
            progresso.update(1)

        with ThreadPoolExecutor(max_workers=workers) as executor:
            executor.map(verificar_e_excluir, plantas)

        progresso.close()
        wikipedia.salvar_cache_e_limpar()
        duracao = time.time() - inicio
        self.stdout.write(self.style.SUCCESS(f"\nProcesso concluído em {duracao:.2f} segundos."))

