import time
from datetime import timedelta
from django.core.management.base import BaseCommand
from mapping.models import PlantaReferencial
from validar.gbif import validar_nome_cientifico  # Certifique-se de ter essa funcao implementada corretamente

class Command(BaseCommand):
    help = "Valida nome científico via API GBIF e atualiza o banco de dados"

    def handle(self, *args, **options):
        plantas = PlantaReferencial.objects.all()
        total = plantas.count()

        if total == 0:
            self.stdout.write("Nenhuma planta encontrada para validação.")
            return

        inicio = time.time()
        processadas = 0
        erros = []

        self.stdout.write("Iniciando validação via GBIF...")

        for planta in plantas.iterator():
            nome = (planta.nome_cientifico_corrigido or planta.nome_cientifico).strip()
            try:
                resultado = validar_nome_cientifico(nome)

                planta.nome_cientifico_valido = resultado.get("nome_valido") or None
                planta.fonte_validacao = resultado.get("fonte") or "GBIF"
                planta.save(update_fields=["nome_cientifico_valido", "fonte_validacao"])
            except Exception as e:
                erros.append((nome, str(e)))

            processadas += 1
            if processadas % 100 == 0 or processadas == total:
                tempo_atual = time.time()
                tempo_passado = tempo_atual - inicio
                estimado_restante = (tempo_passado / processadas) * (total - processadas)
                tempo_restante = timedelta(seconds=int(estimado_restante))
                progresso = (processadas / total) * 100
                self.stdout.write(f"{processadas}/{total} ({progresso:.2f}%) processadas - Tempo restante: {tempo_restante}")

        self.stdout.write(self.style.SUCCESS("Validação concluída."))
        if erros:
            self.stdout.write("\nOcorreram erros em alguns registros:")
            for nome, erro in erros[:20]:  # Limita a exibição para os 20 primeiros
                self.stdout.write(f"- {nome}: {erro}")
            self.stdout.write(f"Total de erros: {len(erros)}")

