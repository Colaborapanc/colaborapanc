from mapping.models import Nivel

niveis = [
    ("Broto Iniciante", 0),
    ("Folhinha Curiosa", 100),
    ("Caçador de PANCs", 250),
    ("Explorador do Cerrado", 450),
    ("Revisor Raiz", 700),
    ("Guardião das Hortas", 1000),
    ("Botânico Mirim", 1400),
    ("Amig@ da Terra", 1850),
    ("Semeador de Saberes", 2350),
    ("Mestre da Araruta", 2900),
    ("Embaixador PANC", 3500),
    ("Curioso Master", 4200),
    ("Etnoecólogo Ninja", 5000),
    ("Raizeiro(a) Digital", 6000),
    ("Enciclopédia Verde", 7200),
    ("Detetive do Mato", 8500),
    ("Campeão Agroecológico", 10000),
    ("Guardião PANC Supremo", 12000),
    ("Lendário do Cerrado", 15000),
    ("Oráculo das PANCs", 20000),
]

for i, (nome, pontos_minimos) in enumerate(niveis, start=1):
    if i < len(niveis):
        pontos_maximos = niveis[i][1] - 1
    else:
        pontos_maximos = 999999

    Nivel.objects.update_or_create(
        numero=i,
        defaults={
            "nome": nome,
            "pontos_minimos": pontos_minimos,
            "pontos_maximos": pontos_maximos,
            "beneficios": "",
            "surpresa_oculta": ""
        }
    )
