"""
Sistema avançado de identificação de plantas com múltiplas fontes:
1. Base de dados customizada (plantas que fogem ao padrão)
2. Google Cloud Vision API
3. PlantNet API (fallback)
4. Plant.id API (fallback final)
"""

import base64
import importlib.util
import io
import json
import math
import os
import time
from typing import Dict, List, Optional, Tuple

import requests
from PIL import Image

def _safe_find_spec(module_name: str) -> bool:
    try:
        return importlib.util.find_spec(module_name) is not None
    except ModuleNotFoundError:
        return False


NUMPY_AVAILABLE = False
np = None
if _safe_find_spec("numpy"):
    import numpy as np
    NUMPY_AVAILABLE = True
else:
    print("[WARNING] NumPy não instalado. Algumas análises locais serão simplificadas.")

# Importações do Google Cloud Vision
GOOGLE_VISION_AVAILABLE = False
vision = None
service_account = None
if _safe_find_spec("google.cloud.vision") and _safe_find_spec("google.oauth2.service_account"):
    from google.cloud import vision
    from google.oauth2 import service_account
    GOOGLE_VISION_AVAILABLE = True
else:
    print("[WARNING] Google Cloud Vision não instalado. Use: pip install google-cloud-vision")


class IdentificadorPlantas:
    """
    Classe principal para identificação de plantas usando múltiplas fontes
    """

    def __init__(self):
        # APIs Keys
        self.plantnet_api_key = os.getenv('PLANTNET_API_KEY', '')
        self.plantid_api_key = os.getenv('PLANTID_API_KEY', '')
        self.google_credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS', '')

        # Inicializar cliente Google Vision
        self.vision_client = None
        if GOOGLE_VISION_AVAILABLE and self.google_credentials_path and os.path.exists(self.google_credentials_path):
            try:
                credentials = service_account.Credentials.from_service_account_file(
                    self.google_credentials_path
                )
                self.vision_client = vision.ImageAnnotatorClient(credentials=credentials)
            except Exception as e:
                print(f"[Google Vision] Erro ao inicializar: {e}")

        # Estatísticas de uso
        self.stats = {
            'custom_db': 0,
            'google_vision': 0,
            'plantnet': 0,
            'plantid': 0,
            'failures': 0
        }

    def identificar(self, image_path_or_bytes, usar_custom_db=True, usar_google=True) -> Dict:
        """
        Método principal de identificação com fallback automático

        Args:
            image_path_or_bytes: Caminho da imagem ou bytes
            usar_custom_db: Se deve tentar base customizada primeiro
            usar_google: Se deve usar Google Vision

        Returns:
            Dict com resultado da identificação
        """
        inicio = time.time()

        # Tentar base de dados customizada primeiro (mais rápido e específico)
        if usar_custom_db:
            resultado = self._identificar_base_customizada(image_path_or_bytes)
            if resultado and resultado['score'] > 0.7:
                resultado['tempo_processamento'] = time.time() - inicio
                self.stats['custom_db'] += 1
                return resultado

        # Tentar Google Cloud Vision
        if usar_google and self.vision_client:
            resultado = self._identificar_google_vision(image_path_or_bytes)
            if resultado and resultado['score'] > 0.6:
                resultado['tempo_processamento'] = time.time() - inicio
                self.stats['google_vision'] += 1
                return resultado

        # Fallback para PlantNet
        resultado = self._identificar_plantnet(image_path_or_bytes)
        if resultado and resultado['score'] > 0.5:
            resultado['tempo_processamento'] = time.time() - inicio
            self.stats['plantnet'] += 1
            return resultado

        # Fallback final para Plant.id
        resultado = self._identificar_plantid(image_path_or_bytes)
        if resultado:
            resultado['tempo_processamento'] = time.time() - inicio
            self.stats['plantid'] += 1
            return resultado

        # Nenhuma API conseguiu identificar
        self.stats['failures'] += 1
        return {
            'metodo': 'nenhum',
            'nome_popular': '',
            'nome_cientifico': '',
            'score': 0.0,
            'erro': 'Nenhuma API conseguiu identificar a planta',
            'tempo_processamento': time.time() - inicio
        }

    def _identificar_base_customizada(self, image_path_or_bytes) -> Optional[Dict]:
        """
        Identifica usando a base de dados customizada local
        Compara características visuais extraídas da imagem
        """
        try:
            from django.core.exceptions import ObjectDoesNotExist
            from mapping.models import PlantaCustomizada

            # Extrair features da imagem
            features = self._extrair_features_imagem(image_path_or_bytes)

            # Buscar plantas customizadas com features similares
            plantas_custom = PlantaCustomizada.objects.filter(
                validado_por_especialista=True,
                features_ml__isnull=False
            )

            melhor_match = None
            melhor_score = 0.0

            for planta in plantas_custom:
                if planta.features_ml:
                    similaridade = self._calcular_similaridade(features, planta.features_ml)
                    if similaridade > melhor_score:
                        melhor_score = similaridade
                        melhor_match = planta

            if melhor_match and melhor_score > 0.7:
                return {
                    'metodo': 'custom_ml',
                    'nome_popular': melhor_match.nome_variacao,
                    'nome_cientifico': melhor_match.planta_base.nome_cientifico,
                    'score': melhor_score,
                    'planta_customizada_id': melhor_match.id,
                    'planta_base_id': melhor_match.planta_base.id,
                    'descricao': melhor_match.descricao
                }
        except Exception as e:
            print(f"[Custom DB] Erro: {e}")

        return None

    def _identificar_google_vision(self, image_path_or_bytes) -> Optional[Dict]:
        """
        Identifica usando Google Cloud Vision API
        """
        if not self.vision_client:
            return None

        try:
            # Preparar imagem para Google Vision
            if isinstance(image_path_or_bytes, bytes):
                content = image_path_or_bytes
            elif isinstance(image_path_or_bytes, str):
                with open(image_path_or_bytes, 'rb') as f:
                    content = f.read()
            else:
                content = image_path_or_bytes.read()

            image = vision.Image(content=content)

            # Executar detecção de labels e web entities
            response = self.vision_client.label_detection(image=image)
            labels = response.label_annotations

            # Também buscar informações web para contexto
            web_response = self.vision_client.web_detection(image=image)
            web_entities = web_response.web_detection.web_entities if web_response.web_detection else []

            # Processar resultados
            plantas_detectadas = []

            # Analisar labels
            for label in labels:
                descricao = label.description.lower()
                # Filtrar apenas labels relacionados a plantas
                palavras_planta = ['plant', 'planta', 'leaf', 'folha', 'flower', 'flor',
                                  'tree', 'árvore', 'herb', 'erva', 'vegetable', 'vegetal']
                if any(palavra in descricao for palavra in palavras_planta):
                    plantas_detectadas.append({
                        'descricao': label.description,
                        'score': label.score
                    })

            # Analisar web entities
            for entity in web_entities[:5]:  # Top 5
                if entity.score > 0.5:
                    plantas_detectadas.append({
                        'descricao': entity.description,
                        'score': entity.score
                    })

            if plantas_detectadas:
                # Ordenar por score
                plantas_detectadas.sort(key=lambda x: x['score'], reverse=True)
                melhor = plantas_detectadas[0]

                # Tentar encontrar correspondência no banco
                nome_identificado = melhor['descricao']
                planta_ref = self._buscar_planta_por_nome(nome_identificado)

                return {
                    'metodo': 'google_vision',
                    'nome_popular': planta_ref['nome_popular'] if planta_ref else nome_identificado,
                    'nome_cientifico': planta_ref['nome_cientifico'] if planta_ref else '',
                    'score': float(melhor['score']),
                    'planta_base_id': planta_ref['id'] if planta_ref else None,
                    'labels_adicionais': [p['descricao'] for p in plantas_detectadas[1:4]]
                }

        except Exception as e:
            print(f"[Google Vision] Erro: {e}")

        return None

    def _identificar_plantnet(self, image_path_or_bytes) -> Optional[Dict]:
        """
        Identifica usando PlantNet API
        """
        try:
            url = "https://my-api.plantnet.org/v2/identify/all"

            if isinstance(image_path_or_bytes, str):
                files = {'images': open(image_path_or_bytes, 'rb')}
            elif isinstance(image_path_or_bytes, bytes):
                files = {'images': io.BytesIO(image_path_or_bytes)}
            else:
                files = {'images': image_path_or_bytes}

            data = {'organs': 'leaf'}
            params = {'api-key': self.plantnet_api_key}

            response = requests.post(url, files=files, data=data, params=params, timeout=30)

            if response.status_code == 200:
                results = response.json().get('results', [])
                if results:
                    best = results[0]
                    species = best.get('species', {})

                    nome_cientifico = species.get('scientificNameWithoutAuthor', '')
                    nome_popular = species.get('commonNames', [''])[0] if species.get('commonNames') else ''

                    # Buscar no banco de dados
                    planta_ref = self._buscar_planta_por_nome(nome_cientifico) or \
                                 self._buscar_planta_por_nome(nome_popular)

                    return {
                        'metodo': 'plantnet',
                        'nome_popular': nome_popular,
                        'nome_cientifico': nome_cientifico,
                        'score': float(best.get('score', 0.0)),
                        'planta_base_id': planta_ref['id'] if planta_ref else None,
                        'url': species.get('gbif', '')
                    }

        except Exception as e:
            print(f"[PlantNet] Erro: {e}")

        return None

    def _identificar_plantid(self, image_path_or_bytes) -> Optional[Dict]:
        """
        Identifica usando Plant.id API
        """
        try:
            url = "https://api.plant.id/v2/identify"
            headers = {"Api-Key": self.plantid_api_key}

            # Preparar imagem em base64
            if isinstance(image_path_or_bytes, str):
                with open(image_path_or_bytes, 'rb') as f:
                    image_data = base64.b64encode(f.read()).decode()
            elif isinstance(image_path_or_bytes, bytes):
                image_data = base64.b64encode(image_path_or_bytes).decode()
            else:
                image_data = base64.b64encode(image_path_or_bytes.read()).decode()

            payload = {
                "images": [f"data:image/jpeg;base64,{image_data}"],
                "modifiers": ["crops_fast", "similar_images"],
                "plant_details": ["common_names", "url", "taxonomy", "description"]
            }

            response = requests.post(url, json=payload, headers=headers, timeout=30)

            if response.status_code == 200:
                data = response.json()
                if data.get('suggestions'):
                    best = data['suggestions'][0]
                    plant_details = best.get('plant_details', {})

                    nome_cientifico = best.get('plant_name', '')
                    nomes_populares = plant_details.get('common_names', [])
                    nome_popular = nomes_populares[0] if nomes_populares else ''

                    # Buscar no banco
                    planta_ref = self._buscar_planta_por_nome(nome_cientifico) or \
                                 self._buscar_planta_por_nome(nome_popular)

                    return {
                        'metodo': 'plantid',
                        'nome_popular': nome_popular,
                        'nome_cientifico': nome_cientifico,
                        'score': float(best.get('probability', 0.0)),
                        'planta_base_id': planta_ref['id'] if planta_ref else None,
                        'url': plant_details.get('url', '')
                    }

        except Exception as e:
            print(f"[Plant.id] Erro: {e}")

        return None

    def _extrair_features_imagem(self, image_path_or_bytes) -> Dict:
        """
        Extrai características visuais da imagem para comparação
        (histograma de cores, textura, etc)
        """
        try:
            # Abrir imagem
            if isinstance(image_path_or_bytes, str):
                img = Image.open(image_path_or_bytes)
            elif isinstance(image_path_or_bytes, bytes):
                img = Image.open(io.BytesIO(image_path_or_bytes))
            else:
                img = Image.open(image_path_or_bytes)

            # Redimensionar para padronização
            img = img.resize((224, 224))

            if NUMPY_AVAILABLE:
                img_array = np.array(img)
                # Extrair features simples
                features = {
                    # Histograma de cores (RGB)
                    'hist_r': np.histogram(img_array[:, :, 0], bins=32)[0].tolist() if len(img_array.shape) > 2 else [],
                    'hist_g': np.histogram(img_array[:, :, 1], bins=32)[0].tolist() if len(img_array.shape) > 2 else [],
                    'hist_b': np.histogram(img_array[:, :, 2], bins=32)[0].tolist() if len(img_array.shape) > 2 else [],

                    # Cor média
                    'cor_media': img_array.mean(axis=(0, 1)).tolist(),

                    # Desvio padrão (textura aproximada)
                    'textura_std': img_array.std(axis=(0, 1)).tolist(),
                }
            else:
                img = img.convert("RGB")
                pixels = list(img.getdata())
                hist_r = self._calcular_histograma(pixels, 0)
                hist_g = self._calcular_histograma(pixels, 1)
                hist_b = self._calcular_histograma(pixels, 2)
                media_r, std_r = self._calcular_media_std(pixels, 0)
                media_g, std_g = self._calcular_media_std(pixels, 1)
                media_b, std_b = self._calcular_media_std(pixels, 2)
                features = {
                    'hist_r': hist_r,
                    'hist_g': hist_g,
                    'hist_b': hist_b,
                    'cor_media': [media_r, media_g, media_b],
                    'textura_std': [std_r, std_g, std_b],
                }

            return features

        except Exception as e:
            print(f"[Features] Erro ao extrair: {e}")
            return {}

    def _calcular_similaridade(self, features1: Dict, features2: Dict) -> float:
        """
        Calcula similaridade entre duas features usando distância de histogramas
        """
        try:
            # Comparar histogramas
            if not features1 or not features2:
                return 0.0

            similaridades = []

            # Similaridade de histogramas RGB
            for canal in ['hist_r', 'hist_g', 'hist_b']:
                if canal in features1 and canal in features2:
                    if NUMPY_AVAILABLE:
                        hist1 = np.array(features1[canal])
                        hist2 = np.array(features2[canal])

                        # Normalizar
                        hist1 = hist1 / (hist1.sum() + 1e-10)
                        hist2 = hist2 / (hist2.sum() + 1e-10)

                        # Distância chi-quadrado invertida
                        chi_squared = np.sum((hist1 - hist2) ** 2 / (hist1 + hist2 + 1e-10))
                    else:
                        hist1 = features1[canal]
                        hist2 = features2[canal]
                        soma1 = sum(hist1) + 1e-10
                        soma2 = sum(hist2) + 1e-10
                        hist1_norm = [h / soma1 for h in hist1]
                        hist2_norm = [h / soma2 for h in hist2]
                        chi_squared = 0.0
                        for h1, h2 in zip(hist1_norm, hist2_norm):
                            chi_squared += (h1 - h2) ** 2 / (h1 + h2 + 1e-10)

                    similaridade = 1.0 / (1.0 + chi_squared)
                    similaridades.append(similaridade)

            # Similaridade de cor média
            if 'cor_media' in features1 and 'cor_media' in features2:
                if NUMPY_AVAILABLE:
                    cor1 = np.array(features1['cor_media'])
                    cor2 = np.array(features2['cor_media'])
                    dist_cor = np.linalg.norm(cor1 - cor2)
                else:
                    cor1 = features1['cor_media']
                    cor2 = features2['cor_media']
                    dist_cor = math.sqrt(sum((c1 - c2) ** 2 for c1, c2 in zip(cor1, cor2)))
                similaridade_cor = 1.0 / (1.0 + dist_cor / 255.0)
                similaridades.append(similaridade_cor)

            # Retornar média das similaridades
            if not similaridades:
                return 0.0
            if NUMPY_AVAILABLE:
                return float(np.mean(similaridades))
            return sum(similaridades) / len(similaridades)

        except Exception as e:
            print(f"[Similaridade] Erro: {e}")
            return 0.0

    def _buscar_planta_por_nome(self, nome: str) -> Optional[Dict]:
        """
        Busca planta no banco de dados por nome popular ou científico
        """
        try:
            from mapping.models import PlantaReferencial
            from django.db.models import Q

            if not nome:
                return None

            # Buscar por nome (case-insensitive)
            planta = PlantaReferencial.objects.filter(
                Q(nome_popular__icontains=nome) |
                Q(nome_cientifico__icontains=nome) |
                Q(nome_cientifico_valido__icontains=nome)
            ).first()

            if planta:
                return {
                    'id': planta.id,
                    'nome_popular': planta.nome_popular,
                    'nome_cientifico': planta.nome_cientifico,
                    'parte_comestivel': planta.parte_comestivel,
                    'forma_uso': planta.forma_uso
                }

        except Exception as e:
            print(f"[Buscar Planta] Erro: {e}")

        return None

    @staticmethod
    def _calcular_histograma(pixels: List[Tuple[int, int, int]], canal: int, bins: int = 32) -> List[int]:
        hist = [0] * bins
        if not pixels:
            return hist

        for pixel in pixels:
            valor = pixel[canal]
            indice = min(valor * bins // 256, bins - 1)
            hist[indice] += 1
        return hist

    @staticmethod
    def _calcular_media_std(pixels: List[Tuple[int, int, int]], canal: int) -> Tuple[float, float]:
        if not pixels:
            return 0.0, 0.0
        total = sum(pixel[canal] for pixel in pixels)
        n = len(pixels)
        media = total / n
        variancia = sum((pixel[canal] - media) ** 2 for pixel in pixels) / n
        return media, math.sqrt(variancia)

    def get_estatisticas(self) -> Dict:
        """
        Retorna estatísticas de uso das APIs
        """
        total = sum(self.stats.values())
        if total == 0:
            return self.stats

        return {
            **self.stats,
            'total': total,
            'taxa_sucesso': (total - self.stats['failures']) / total * 100
        }


# Função de conveniência para uso direto
def identificar_planta(image_path_or_bytes, usar_custom_db=True, usar_google=True) -> Dict:
    """
    Função helper para identificar planta
    """
    identificador = IdentificadorPlantas()
    return identificador.identificar(image_path_or_bytes, usar_custom_db, usar_google)
