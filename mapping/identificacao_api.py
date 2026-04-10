import logging
import os
from contextlib import contextmanager

import requests

logger = logging.getLogger(__name__)


@contextmanager
def _arquivo_imagem(foto):
    if hasattr(foto, "read"):
        try:
            foto.seek(0)
        except Exception:
            logger.debug("Não foi possível resetar o cursor da imagem.")
        yield foto
    else:
        arquivo = open(foto, "rb")
        try:
            yield arquivo
        finally:
            arquivo.close()

def identificar_plantnet(foto, project='all'):
    """
    Consulta a API PlantNet com a foto enviada.
    Retorna um dicionário com informações ou {} se não encontrar nada.
    """
    url = f"https://my-api.plantnet.org/v2/identify/{project}"
    api_key = os.environ.get("PLANTNET_API_KEY")

    if not api_key:
        logger.warning("[PlantNet] PLANTNET_API_KEY não configurada. Pulando identificação PlantNet.")
        return {}

    data = {'organs': 'leaf'}

    try:
        with _arquivo_imagem(foto) as arquivo:
            files = {'images': arquivo}
            resp = requests.post(
                url,
                files=files,
                data=data,
                params={'api-key': api_key},
                timeout=15,
            )

        logger.info("[PlantNet] Status HTTP: %s", resp.status_code)

        if resp.status_code == 200:
            json_data = resp.json()
            results = json_data.get('results', [])

            if results:
                best = results[0]
                species = best.get('species', {})

                resultado = {
                    'fonte': 'Pl@ntNet',
                    'nome_popular': species.get('commonNames', [''])[0] if species.get('commonNames') else '',
                    'nome_cientifico': species.get('scientificNameWithoutAuthor', ''),
                    'score': best.get('score', 0.0),
                    'url': species.get('gbif', '')
                }

                logger.info("[PlantNet] Identificação bem-sucedida: %s (score: %.2f)",
                          resultado.get('nome_cientifico') or resultado.get('nome_popular'),
                          resultado.get('score', 0))

                return resultado
            else:
                logger.warning("[PlantNet] Nenhum resultado encontrado na resposta da API")
        elif resp.status_code == 401:
            logger.error("[PlantNet] API Key inválida ou expirada")
        elif resp.status_code == 404:
            logger.error("[PlantNet] Endpoint não encontrado. Verifique o project '%s'", project)
        elif resp.status_code == 429:
            logger.warning("[PlantNet] Limite de requisições excedido")
        else:
            logger.warning("[PlantNet] Resposta inesperada (status %s): %s",
                         resp.status_code, resp.text[:200])

    except requests.exceptions.Timeout:
        logger.warning("[PlantNet] Timeout ao consultar API (>15s)")
    except requests.exceptions.ConnectionError:
        logger.error("[PlantNet] Erro de conexão com a API")
    except requests.exceptions.RequestException as e:
        logger.exception("[PlantNet] Erro na requisição: %s", str(e))
    except Exception as e:
        logger.exception("[PlantNet] Erro inesperado: %s", str(e))

    return {}

def identificar_plantid(foto, api_key):
    """
    Consulta a API Plant.id com a foto enviada.
    Retorna um dicionário com informações ou {} se não encontrar nada.
    """
    url = "https://api.plant.id/v2/identify"
    headers = {"Api-Key": api_key}
    payload = {"organs": ["leaf", "flower"]}

    try:
        with _arquivo_imagem(foto) as arquivo:
            files = {'images': arquivo}
            resp = requests.post(
                url,
                headers=headers,
                files=files,
                data=payload,
                timeout=15,
            )

        logger.info("[Plant.id] Status HTTP: %s", resp.status_code)

        if resp.status_code == 200:
            json_data = resp.json()
            suggestions = json_data.get('suggestions', [])

            if suggestions:
                best = suggestions[0]
                plant_details = best.get('plant_details', {})

                resultado = {
                    'fonte': 'Plant.id',
                    'nome_popular': plant_details.get('common_names', [''])[0] if plant_details.get('common_names') else '',
                    'nome_cientifico': best.get('plant_name', ''),
                    'score': best.get('probability', 0.0),
                    'url': plant_details.get('url', '')
                }

                logger.info("[Plant.id] Identificação bem-sucedida: %s (score: %.2f)",
                          resultado.get('nome_cientifico') or resultado.get('nome_popular'),
                          resultado.get('score', 0))

                return resultado
            else:
                logger.warning("[Plant.id] Nenhuma sugestão encontrada na resposta da API")
        elif resp.status_code == 401:
            logger.error("[Plant.id] API Key inválida ou expirada")
        elif resp.status_code == 402:
            logger.warning("[Plant.id] Créditos da API esgotados")
        elif resp.status_code == 429:
            logger.warning("[Plant.id] Limite de requisições excedido")
        else:
            logger.warning("[Plant.id] Resposta inesperada (status %s): %s",
                         resp.status_code, resp.text[:200])

    except requests.exceptions.Timeout:
        logger.warning("[Plant.id] Timeout ao consultar API (>15s)")
    except requests.exceptions.ConnectionError:
        logger.error("[Plant.id] Erro de conexão com a API")
    except requests.exceptions.RequestException as e:
        logger.exception("[Plant.id] Erro na requisição: %s", str(e))
    except Exception as e:
        logger.exception("[Plant.id] Erro inesperado: %s", str(e))

    return {}

def identificar_planta_api(foto):
    """
    Consulta primeiro o Pl@ntNet; se não identificar, tenta Plant.id.
    Retorna uma lista com o melhor resultado encontrado (ou vazia).
    """
    logger.info("=== Iniciando identificação de planta ===")

    plantnet_api_key = os.environ.get("PLANTNET_API_KEY")
    plantid_api_key = os.environ.get("PLANTID_API_KEY")

    if not plantnet_api_key and not plantid_api_key:
        logger.error("Nenhuma API key configurada (PLANTNET_API_KEY ou PLANTID_API_KEY). Identificação não disponível.")
        return []

    # Tenta PlantNet primeiro
    logger.info("Tentando identificação via PlantNet...")
    resultado_net = identificar_plantnet(foto)
    if resultado_net and (resultado_net.get('nome_cientifico') or resultado_net.get('nome_popular')):
        logger.info("✓ Identificação bem-sucedida via PlantNet")
        return [resultado_net]
    else:
        logger.info("✗ PlantNet não retornou resultados válidos")

    # Fallback para Plant.id
    if plantid_api_key:
        logger.info("Tentando identificação via Plant.id (fallback)...")
        resultado_id = identificar_plantid(foto, plantid_api_key)
        if resultado_id and (resultado_id.get('nome_cientifico') or resultado_id.get('nome_popular')):
            logger.info("✓ Identificação bem-sucedida via Plant.id")
            return [resultado_id]
        else:
            logger.info("✗ Plant.id não retornou resultados válidos")
    else:
        logger.warning("PLANTID_API_KEY não configurada. Pulando fallback para Plant.id.")

    logger.warning("=== Nenhuma API conseguiu identificar a planta ===")
    return []

