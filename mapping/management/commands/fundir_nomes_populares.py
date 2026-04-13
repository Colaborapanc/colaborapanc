from django.core.management.base import BaseCommand
from mapping.models import PlantaReferencial
from django.db import transaction
from collections import defaultdict

class Command(BaseCommand):
    help = 'Funde registros com mesmo nome científico agregando nomes populares distintos'

    def handle(self, *args, **kwargs):
        self.stdout.write("Iniciando fusão de nomes populares...")

        grupos = defaultdict(list)
        plantas = PlantaReferencial.objects.all()

        for planta in plantas:
            grupos[planta.nome_cientifico.strip().lower()].append(planta)

        total_fundidas = 0

        with transaction.atomic():
            for nome_cientifico, registros in grupos.items():
                if len(registros) < 2:
                    continue

                # Ordenar por número de campos preenchidos
                def campos_preenchidos(p):
                    return sum(bool(getattr(p, campo)) for campo in ['grupo_taxonomico', 'origem', 'bioma', 'regiao_ocorrencia', 'fonte'])

                registros.sort(key=campos_preenchidos, reverse=True)
                principal = registros[0]

                nomes_populares = set()
                if principal.nome_popular:
                    nomes_populares.update([n.strip() for n in principal.nome_popular.split(',')])

                for duplicata in registros[1:]:
                    if duplicata.nome_popular:
                        nomes_populares.update([n.strip() for n in duplicata.nome_popular.split(',')])
                    duplicata.delete()

                principal.nome_popular = ', '.join(sorted(nomes_populares))
                principal.save()
                total_fundidas += 1

        self.stdout.write(self.style.SUCCESS(f"Fusão concluída: {total_fundidas} registros fundidos."))
