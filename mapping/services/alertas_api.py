import feedparser
from datetime import datetime, timedelta
from mapping.models import PontoPANC, AlertaClimatico

# URL do feed RSS do INMET
RSS_FEED_URL = "https://alertas2.inmet.gov.br/rss/avisos/rss.xml"

def buscar_alertas_rss():
    """Obtém os alertas do feed RSS do INMET"""
    try:
        feed = feedparser.parse(RSS_FEED_URL)
        return feed.entries
    except Exception as e:
        print(f"[RSS] Erro ao obter feed: {e}")
        return []

def extrair_dados_alerta(entry):
    """Extrai título, descrição, data de início e fim do alerta"""
    try:
        title = entry.title
        summary = entry.summary
        published = datetime(*entry.published_parsed[:6]).date()

        # Tentativa de extração da data de fim (caso mencionada)
        if "até" in summary:
            partes = summary.split("até")
            fim_str = partes[-1].strip().split("<")[0].strip()
            try:
                fim = datetime.strptime(fim_str, "%d/%m/%Y").date()
            except ValueError:
                fim = published + timedelta(days=1)
        else:
            fim = published + timedelta(days=1)

        return title.strip(), summary.strip(), published, fim
    except Exception as e:
        print(f"[RSS] Erro ao extrair dados do alerta: {e}")
        return None, None, None, None

def salvar_alertas_para_pontos(entries):
    """Associa cada alerta a todos os pontos com coordenadas válidas"""
    total_salvos = 0
    for entry in entries:
        tipo, descricao, inicio, fim = extrair_dados_alerta(entry)
        if not tipo or not inicio:
            continue

        pontos_com_coords = PontoPANC.objects.exclude(latitude=None).exclude(longitude=None)

        for ponto in pontos_com_coords:
            alerta_existe = AlertaClimatico.objects.filter(
                ponto=ponto,
                tipo=tipo,
                inicio=inicio,
                fim=fim
            ).exists()

            if not alerta_existe:
                AlertaClimatico.objects.create(
                    ponto=ponto,
                    tipo=tipo,
                    descricao=descricao,
                    inicio=inicio,
                    fim=fim,
                    fonte="INMET-RSS"
                )
                total_salvos += 1
                print(f"[✅] Alerta RSS salvo para: {ponto.nome_popular} ({ponto.estado})")

    print(f"[✅] Total de alertas RSS salvos: {total_salvos}")

def atualizar_alertas_rss():
    """Executa a rotina de atualização dos alertas INMET via RSS"""
    print("[🌐] Buscando alertas via RSS do INMET...")
    entries = buscar_alertas_rss()
    salvar_alertas_para_pontos(entries)
    print("[🔄] Finalizado.")
