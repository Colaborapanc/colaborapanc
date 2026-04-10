import requests
from datetime import datetime
from django.utils.timezone import make_aware
from mapping.models import PontoPANC, AlertaClimatico

def atualizar_alertas_openmeteo():
    print("[🌍] Buscando alertas do Open-Meteo...")

    pontos = PontoPANC.objects.exclude(latitude=None).exclude(longitude=None)
    total_alertas = 0

    for ponto in pontos:
        try:
            lat, lon = ponto.latitude, ponto.longitude

            url = (
                f"https://api.open-meteo.com/v1/forecast?"
                f"latitude={lat}&longitude={lon}&daily=weathercode,temperature_2m_max,precipitation_sum"
                f"&alerts=true&timezone=America/Sao_Paulo"
            )

            response = requests.get(url, timeout=10)
            if not response.ok:
                print(f"[⚠️] Falha na resposta para {ponto.nome_popular}: {response.status_code}")
                continue

            data = response.json()
            alertas = data.get("alerts", [])

            for alerta in alertas:
                descricao = alerta.get("description", "Sem descrição")
                tipo = alerta.get("event", "Evento não especificado")
                inicio = alerta.get("onset") or alerta.get("start")
                fim = alerta.get("expires") or alerta.get("end")

                try:
                    dt_inicio = make_aware(datetime.fromisoformat(inicio)) if inicio else None
                    dt_fim = make_aware(datetime.fromisoformat(fim)) if fim else None
                except Exception as e:
                    print(f"[⚠️] Erro ao converter datas para {ponto.nome_popular}: {e}")
                    continue

                if not (dt_inicio and dt_fim):
                    continue

                alerta_existe = AlertaClimatico.objects.filter(
                    ponto=ponto,
                    tipo=tipo,
                    inicio=dt_inicio.date(),
                    fim=dt_fim.date(),
                    fonte="OPEN_METEO"
                ).exists()

                if not alerta_existe:
                    AlertaClimatico.objects.create(
                        ponto=ponto,
                        tipo=tipo,
                        descricao=descricao,
                        inicio=dt_inicio.date(),
                        fim=dt_fim.date(),
                        fonte="OPEN_METEO"
                    )
                    total_alertas += 1
                    print(f"[✅] Alerta salvo para {ponto.nome_popular} ({tipo})")

        except Exception as e:
            print(f"[❌] Erro no ponto {ponto.nome_popular}: {e}")

    print(f"[✅] Total de alertas Open-Meteo salvos: {total_alertas}")
    print("[🔄] Finalizado.")
