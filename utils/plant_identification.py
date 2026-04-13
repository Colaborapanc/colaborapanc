import os
import requests
from datetime import datetime
from django.conf import settings
from mapping.models import APIUsageLog

# --- CONFIGURAÇÕES ---
# IMPORTANTE: Configure as variáveis de ambiente PLANTID_API_KEY e PLANTNET_API_KEY
PLANTID_API_KEY = os.getenv('PLANTID_API_KEY', '')
PLANTNET_API_KEY = os.getenv('PLANTNET_API_KEY', '')

PLANTID_MONTHLY_LIMIT = 50      # Exemplo: plano gratuito (ajuste conforme necessidade)
PLANTNET_MONTHLY_LIMIT = 1000   # Exemplo: limite institucional

# --- FUNÇÕES AUXILIARES DE CONTROLE DE USO ---

def get_month():
    """Retorna string 'YYYY-MM' do mês atual."""
    return datetime.now().strftime('%Y-%m')

def get_or_create_api_log(api_name, limit):
    month = get_month()
    log, created = APIUsageLog.objects.get_or_create(
        api_name=api_name,
        month=month,
        defaults={'limit': limit, 'used': 0}
    )
    # Se limite mudou, atualize
    if not created and log.limit != limit:
        log.limit = limit
        log.save()
    return log

def increment_api_usage(api_name, limit):
    log = get_or_create_api_log(api_name, limit)
    log.used += 1
    log.save()

def can_use_api(api_name, limit):
    log = get_or_create_api_log(api_name, limit)
    return log.used < log.limit

def get_api_usage(api_name):
    """Retorna (usados, limite)"""
    log = get_or_create_api_log(api_name, PLANTID_MONTHLY_LIMIT if api_name == 'Plant.id' else PLANTNET_MONTHLY_LIMIT)
    return log.used, log.limit

# --- INTEGRAÇÃO PLANT.ID ---

def call_plant_id_api(image_path):
    url = "https://api.plant.id/v2/identify"
    headers = {
        'Content-Type': 'application/json',
        'Api-Key': PLANTID_API_KEY,
    }
    # Leia a imagem e converta para base64
    import base64
    with open(image_path, "rb") as img_file:
        img_b64 = base64.b64encode(img_file.read()).decode()
    payload = {
        "images": [img_b64],
        "organs": ["leaf", "flower", "fruit", "bark"],  # Tente todos para aumentar chance
        "details": ["common_names", "taxonomy"],
    }
    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=30)
        resp.raise_for_status()
        result = resp.json()
        # Pegue o resultado mais provável
        suggestions = result.get('suggestions', [])
        if suggestions:
            # Pega o nome científico e popular (se disponível)
            nome_cientifico = suggestions[0]['plant_details']['scientific_name']
            nomes_populares = suggestions[0]['plant_details'].get('common_names', [])
            return {
                'success': True,
                'nome_cientifico': nome_cientifico,
                'nomes_populares': nomes_populares,
                'raw': result,
            }
        return {'success': False, 'error': 'Sem sugestões', 'raw': result}
    except Exception as e:
        return {'success': False, 'error': str(e)}

# --- INTEGRAÇÃO PLANTNET ---

def call_plantnet_api(image_path):
    url = f"https://my-api.plantnet.org/v2/identify/all?api-key={PLANTNET_API_KEY}"
    files = {'images': open(image_path, 'rb')}
    data = {'organs': 'auto'}
    try:
        resp = requests.post(url, files=files, data=data, timeout=30)
        resp.raise_for_status()
        result = resp.json()
        results = result.get('results', [])
        if results:
            # Pega o nome científico mais provável
            nome_cientifico = results[0]['species']['scientificNameWithoutAuthor']
            nomes_populares = results[0]['species'].get('commonNames', [])
            return {
                'success': True,
                'nome_cientifico': nome_cientifico,
                'nomes_populares': nomes_populares,
                'raw': result,
            }
        return {'success': False, 'error': 'Sem sugestões', 'raw': result}
    except Exception as e:
        return {'success': False, 'error': str(e)}

# --- FUNÇÃO PRINCIPAL DE FALLBACK ---

def identificar_especie(image_path):
    """Identifica espécie, tentando Plant.id, depois PlantNet, depois fallback."""
    # Primeiro, tente Plant.id
    if can_use_api('Plant.id', PLANTID_MONTHLY_LIMIT):
        resultado = call_plant_id_api(image_path)
        if resultado['success']:
            increment_api_usage('Plant.id', PLANTID_MONTHLY_LIMIT)
            return {
                'nome_cientifico': resultado['nome_cientifico'],
                'nomes_populares': resultado['nomes_populares'],
                'api_usada': 'Plant.id',
                'log': resultado['raw'],
                'mensagem': 'Identificação realizada via Plant.id',
                'fallback': False,
            }
        else:
            increment_api_usage('Plant.id', PLANTID_MONTHLY_LIMIT)  # Contabiliza tentativa

    # Se Plant.id não disponível ou falhou, tente PlantNet
    if can_use_api('PlantNet', PLANTNET_MONTHLY_LIMIT):
        resultado = call_plantnet_api(image_path)
        if resultado['success']:
            increment_api_usage('PlantNet', PLANTNET_MONTHLY_LIMIT)
            return {
                'nome_cientifico': resultado['nome_cientifico'],
                'nomes_populares': resultado['nomes_populares'],
                'api_usada': 'PlantNet',
                'log': resultado['raw'],
                'mensagem': 'Identificação realizada via PlantNet',
                'fallback': True,
            }
        else:
            increment_api_usage('PlantNet', PLANTNET_MONTHLY_LIMIT)

    # Se ambas falharem ou atingirem limite
    return {
        'success': False,
        'api_usada': None,
        'mensagem': 'Limite de uso das APIs atingido ou falha na identificação. Utilize o cadastro manual.',
        'fallback': True,
    }
