# /root/apps/pancsite/mapping/utils/gbif.py

import requests

def validar_nome_gbif(nome):
    """
    Valida um nome científico usando a API do GBIF.
    
    Parâmetros:
    - nome (str): Nome científico da planta.

    Retorna:
    - tuple: (nome_cientifico_corrigido, fonte) se válido, senão (None, None).
    """
    try:
        url = f"https://api.gbif.org/v1/species/match?name={nome}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        # Confiança mínima de 90% para considerar a correspondência válida
        if 'usageKey' in data and data.get('confidence', 0) >= 90:
            nome_validado = data.get('scientificName', '').strip()
            return nome_validado, "GBIF"
        else:
            return None, None
    except requests.RequestException as e:
        print(f"[ERRO GBIF] Falha na requisição: {e}")
        return None, None
    except Exception as e:
        print(f"[ERRO GBIF] Erro inesperado: {e}")
        return None, None
