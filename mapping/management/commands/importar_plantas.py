import csv
from django.core.management.base import BaseCommand
from mapping.models import PlantaReferencial

class Command(BaseCommand):
    help = 'Importa plantas referenciais de um arquivo CSV com verificação e atualização'

    def add_arguments(self, parser):
        parser.add_argument('caminho_arquivo', type=str, help='Caminho para o arquivo CSV')

    def handle(self, *args, **kwargs):
        caminho_arquivo = kwargs['caminho_arquivo']
        novos, atualizados, ignorados = 0, 0, 0

        with open(caminho_arquivo, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile, delimiter=';')
            for row in reader:
                nome_cientifico = row.get('nome_cientifico', '').strip()
                nome_popular = row.get('nome_popular', '').strip()

                # Ignorar se não tiver nome científico
                if not nome_cientifico:
                    ignorados += 1
                    continue

                # Usar nome científico como nome popular se este estiver vazio
                if not nome_popular:
                    nome_popular = nome_cientifico

                # Verificar se já existe uma planta com esse nome científico ou popular
                planta_existente = PlantaReferencial.objects.filter(
                    nome_cientifico__iexact=nome_cientifico
                ).first()

                if not planta_existente:
                    planta_existente = PlantaReferencial.objects.filter(
                        nome_popular__iexact=nome_popular
                    ).first()

                if planta_existente:
                    # Atualiza apenas se novos dados estiverem mais completos
                    alterado = False
                    for campo in ['grupo_taxonomico', 'origem', 'bioma', 'regiao_ocorrencia', 'fonte']:
                        valor_csv = row.get(campo, '').strip()
                        if valor_csv and (not getattr(planta_existente, campo, '')):
                            setattr(planta_existente, campo, valor_csv)
                            alterado = True
                    if alterado:
                        planta_existente.save()
                        atualizados += 1
                    else:
                        ignorados += 1
                else:
                    PlantaReferencial.objects.create(
                        nome_popular=nome_popular,
                        nome_cientifico=nome_cientifico,
                        grupo_taxonomico=row.get('grupo_taxonomico', '').strip(),
                        origem=row.get('origem', '').strip(),
                        bioma=row.get('bioma', '').strip(),
                        regiao_ocorrencia=row.get('regiao_ocorrencia', '').strip(),
                        fonte=row.get('fonte', '').strip(),
                    )
                    novos += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Importação concluída: {novos + atualizados} processados | {novos} novos | {atualizados} atualizados | {ignorados} ignorados"
            )
        )
