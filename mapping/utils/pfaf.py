# /root/apps/pancsite/mapping/utils/pfaf.py
import requests
from bs4 import BeautifulSoup
import time

BASE_URL = "https://pfaf.org/user/Plant.aspx?LatinName="


def verificar_pfaf(nome_cientifico):
    """
    Busca informações botânicas e de uso comestível na PFAF.org.
    Retorna um dicionário com 'parte' e 'uso', ou None se não encontrar.
    """
    try:
        url = BASE_URL + nome_cientifico.replace(" ", "+")
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')

        # Busca por seções relevantes
        body_text = soup.find("div", {"id": "plantDetails"})
        if not body_text:
            return None

        texto = body_text.get_text(separator="\n").lower()

        partes_possiveis = ["leaf", "root", "seed", "fruit", "stem", "shoot", "flower", "tuber", "rhizome"]
        usos_possiveis = ["raw", "cooked", "tea", "flour", "starch", "fermented", "edible", "food", "drink"]

        parte_encontrada = next((parte for parte in partes_possiveis if parte in texto), None)
        uso_encontrado = next((uso for uso in usos_possiveis if uso in texto), None)

        if parte_encontrada or uso_encontrado:
            return {
                'parte': parte_encontrada.capitalize() if parte_encontrada else '',
                'uso': uso_encontrado.capitalize() if uso_encontrado else ''
            }

        return None

    except requests.RequestException as e:
        print(f"[ERRO PFAF] Falha na requisição: {e}")
        return None
    except Exception as e:
        print(f"[ERRO PFAF] Erro inesperado: {e}")
        return None
