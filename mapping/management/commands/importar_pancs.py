import csv
import os
from django.core.management.base import BaseCommand
from mapping.models import PlantaReferencial

class Command(BaseCommand):
    help = 'Importa dados de Pancs.csv para o modelo PlantaReferencial'

    def handle(self, *args, **kwargs):
        csv_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'Pancs.csv')
        with open(csv_path, encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter=',')
            count = 0
            for row in reader:
                normalized = {k.strip().lower(): v.strip() for k, v in row.items()}
                PlantaReferencial.objects.update_or_create(
                    nome_popular=normalized.get('nome popular', ''),
                    defaults={
                        'nome_cientifico': normalized.get('nome científico', ''),
                        'parte_comestivel': normalized.get('parte comestível', ''),
                        'forma_uso': normalized.get('uso principal', ''),
                    }
                )
                count += 1
            self.stdout.write(self.style.SUCCESS(f'{count} plantas importadas com sucesso.'))
