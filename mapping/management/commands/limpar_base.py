from django.core.management.base import BaseCommand
from mapping.models import PlantaReferencial
import re

class Command(BaseCommand):
    help = 'Limpa e organiza os dados já existentes na tabela PlantaReferencial'

    def normalize(self, text):
        if not text:
            return ''
        # Remove espaços em excesso, quebras de linha e caracteres invisíveis
        text = re.sub(r'\s+', ' ', text).strip()
        # Remove caracteres ilegíveis ou corrompidos
        text = re.sub(r'[^\x00-\x7F]+', '', text)
        return text

    def handle(self, *args, **options):
        registros = PlantaReferencial.objects.all()
        total = registros.count()
        atualizados = 0

        for planta in registros:
            original = (planta.nome_popular, planta.nome_cientifico)

            planta.nome_popular = self.normalize(planta.nome_popular).title()
            planta.nome_cientifico = self.normalize(planta.nome_cientifico).lower()
            planta.parte_comestivel = self.normalize(planta.parte_comestivel)
            planta.forma_uso = self.normalize(planta.forma_uso)

            # Preencher nome_cientifico se vazio mas nome_popular parece válido
            if not planta.nome_cientifico and re.match(r'^[A-Z][a-z]+\s[a-z]+$', planta.nome_popular):
                planta.nome_cientifico = planta.nome_popular.lower()
                planta.nome_popular = ''

            # Preencher nome_popular se vazio
            if not planta.nome_popular:
                planta.nome_popular = planta.nome_cientifico.title()

            if (planta.nome_popular, planta.nome_cientifico) != original:
                planta.save()
                atualizados += 1

        self.stdout.write(self.style.SUCCESS(
            f"Limpeza concluída: {atualizados} registros atualizados de {total} processados."
        ))
