# /root/apps/pancsite/mapping/management/commands/processar_plantas.py

import time
import logging
import csv
import json
from django.core.management.base import BaseCommand
from mapping.models import PlantaReferencial
from mapping.utils import wikipedia
from mapping.utils.gbif import validar_nome_gbif  # certifique-se de que este arquivo existe
from mapping.utils.pfaf import verificar_pfaf     # certifique-se de que este arquivo existe
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm

logging.basicConfig(
    filename='/root/apps/pancsite/logs/log_processamento.txt',  # Diretório separado para logs
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class Command(BaseCommand):
    help = 'Pipeline completo de validação e enriquecimento das plantas'

    def add_arguments(self, parser):
        parser.add_argument('--workers', type=int, default=8, help='Número de threads')
        parser.add_argument('--skip-wikipedia', action='store_true', help='Pular verificação via Wikipedia')
        parser.add_argument('--skip-gbif', action='store_true', help='Pular validação taxonômica via GBIF')
        parser.add_argument('--skip-pfaf', action='store_true', help='Pular verificação botânica via PFAF')
        parser.add_argument('--dry-run', action='store_true', help='Executar sem excluir registros')
        parser.add_argument('--export-csv', type=str, help='Caminho para exportar dados finais')

    def handle(self, *args, **options):
        inicio = time.time()
        plantas = list(PlantaReferencial.objects.all())
        total = len(plantas)
        self.stdout.write(self.style.WARNING(f"\nIniciando processamento de {total} registros com {options['workers']} threads...\n"))
        progresso = tqdm(total=total, desc="Processando", unit="planta")

        def processar(planta):
            try:
                nome_base = planta.nome_cientifico or planta.nome_popular
                nome_base = nome_base.strip()

                # Wikipedia
                if not options['skip_wikipedia']:
                    if not wikipedia.verificar_comestibilidade(nome_base):
                        if not options['dry_run']:
                            PlantaReferencial.objects.filter(id=planta.id).delete()
                        logging.info(f"Excluído (Wikipedia): {nome_base} - ID {planta.id}")
                        progresso.update(1)
                        return

                # GBIF
                if not options['skip_gbif'] and planta.nome_cientifico:
                    nome_valido, fonte = validar_nome_gbif(planta.nome_cientifico)
                    if nome_valido and nome_valido != planta.nome_cientifico:
                        planta.nome_cientifico_corrigido = nome_valido
                        planta.fonte_validacao = fonte

                # PFAF
                if not options['skip_pfaf']:
                    resultado = verificar_pfaf(nome_base)
                    if resultado:
                        planta.parte_comestivel = resultado.get('parte')
                        planta.forma_uso = resultado.get('uso')

                # Normalização
                planta.nome_popular = planta.nome_popular.strip().title() if planta.nome_popular else ""
                planta.nome_cientifico = planta.nome_cientifico.strip().title() if planta.nome_cientifico else ""

                if not options['dry_run']:
                    planta.save()
            except Exception as e:
                logging.error(f"Erro ao processar planta ID {planta.id}: {e}")
            finally:
                progresso.update(1)

        with ThreadPoolExecutor(max_workers=options['workers']) as executor:
            executor.map(processar, plantas)

        progresso.close()
        wikipedia.salvar_cache_e_limpar()

        # Exporta CSV final se solicitado
        if options['export_csv']:
            campos = [f.name for f in PlantaReferencial._meta.fields]
            with open(options['export_csv'], 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(campos)
                for planta in PlantaReferencial.objects.all():
                    writer.writerow([getattr(planta, campo) for campo in campos])
            self.stdout.write(self.style.SUCCESS(f"\nCSV exportado para: {options['export_csv']}"))

        duracao = time.time() - inicio
        self.stdout.write(self.style.SUCCESS(f"\nProcesso completo em {duracao:.2f} segundos."))
