"""
Views para gerenciamento de plantas offline seletivas
Permite que usuários escolham plantas específicas para download offline
"""
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count, Prefetch, Value, IntegerField, Case, When
from django.db.models.functions import Lower
from django.utils import timezone
from django.core.files.base import ContentFile
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
import json
import base64
import logging
import unicodedata
import re

from .models import (
    PlantaReferencial,
    PlantaCustomizada,
    PlantaOfflineUsuario,
    PacotePlantasOffline,
    ConfiguracaoOffline,
    ModeloAR,
    HistoricoIdentificacao
)
from .serializers import PlantaReferencialSerializer
from mapping.services.biodiversity.gbif import GBIFService
from mapping.services.biodiversity.inaturalist import INaturalistService

logger = logging.getLogger(__name__)


def _normalizar_texto(texto):
    """Remove acentos, normaliza caixa e espaços duplicados."""
    if not texto:
        return ''
    texto = unicodedata.normalize('NFKD', texto)
    texto = ''.join(c for c in texto if not unicodedata.combining(c))
    texto = re.sub(r'\s+', ' ', texto).strip().lower()
    return texto


def _calcular_relevancia(planta, termo_normalizado):
    """Calcula score de relevância para ordenação."""
    score = 0
    nome_pop = _normalizar_texto(planta.nome_popular)
    nome_cient = _normalizar_texto(planta.nome_cientifico)

    # Correspondência exata
    if nome_pop == termo_normalizado:
        score += 100
    elif nome_cient == termo_normalizado:
        score += 95

    # Começa com o termo
    if nome_pop.startswith(termo_normalizado):
        score += 50
    elif nome_cient.startswith(termo_normalizado):
        score += 45

    # Contém o termo
    if termo_normalizado in nome_pop:
        score += 20
    if termo_normalizado in nome_cient:
        score += 18

    # Busca em nomes populares consolidados (JSONField list)
    nomes_populares = planta.nomes_populares or []
    for np in nomes_populares:
        np_norm = _normalizar_texto(np)
        if np_norm == termo_normalizado:
            score += 80
        elif termo_normalizado in np_norm:
            score += 15

    # Busca em aliases
    aliases = planta.aliases or []
    for alias in aliases:
        alias_norm = _normalizar_texto(alias)
        if alias_norm == termo_normalizado:
            score += 70
        elif termo_normalizado in alias_norm:
            score += 12

    # Busca em sinônimos
    sinonimos = planta.sinonimos or []
    for sin in sinonimos:
        sin_norm = _normalizar_texto(sin)
        if sin_norm == termo_normalizado:
            score += 60
        elif termo_normalizado in sin_norm:
            score += 10

    # Busca no nome aceito
    nome_aceito = _normalizar_texto(planta.nome_aceito or '')
    if nome_aceito and termo_normalizado in nome_aceito:
        score += 15

    # Bonus para dados enriquecidos
    if planta.is_fully_enriched:
        score += 3
    if planta.status_enriquecimento == 'completo':
        score += 2

    return score


def _merge_list_values(base_values, new_values, limit=30):
    merged = []
    seen = set()
    for value in (base_values or []) + (new_values or []):
        txt = (value or '').strip()
        if not txt:
            continue
        key = _normalizar_texto(txt)
        if key in seen:
            continue
        seen.add(key)
        merged.append(txt)
        if len(merged) >= limit:
            break
    return merged


def _species_dedupe_key(item):
    nome_cientifico = item.get('nome_cientifico_valido') or item.get('nome_cientifico') or ''
    nome_cientifico = _normalizar_texto(nome_cientifico)
    if nome_cientifico:
        return f"nc:{nome_cientifico}"
    return f"id:{item.get('id') or item.get('plataforma_id') or ''}"


def _fonte_score(item):
    fonte = _normalizar_texto(item.get('fonte_resultado') or item.get('origem_integracao') or item.get('fonte') or '')
    if 'referencial' in fonte:
        return 4
    if 'gbif' in fonte:
        return 3
    if 'inaturalist' in fonte:
        return 2
    return 1


def _completeness_score(item):
    fields = [
        'nome_popular', 'nome_cientifico', 'familia', 'parte_comestivel', 'forma_uso',
        'frutificacao', 'colheita', 'bioma', 'regiao'
    ]
    score = sum(1 for field in fields if item.get(field))
    score += len(item.get('sinonimos') or []) * 0.1
    score += len(item.get('nomes_populares') or []) * 0.1
    return score


def _merge_species(base, new_item):
    merged = dict(base or {})
    merged['id'] = merged.get('id') or new_item.get('id')
    merged['internal_id'] = merged.get('internal_id') or new_item.get('internal_id')
    merged['external_id'] = merged.get('external_id') or new_item.get('external_id')
    merged['download_id'] = merged.get('download_id') or new_item.get('download_id')
    merged['stable_id'] = merged.get('stable_id') or new_item.get('stable_id')
    merged['plataforma_id'] = merged.get('plataforma_id') or new_item.get('plataforma_id') or new_item.get('id')
    merged['nome_popular'] = merged.get('nome_popular') or new_item.get('nome_popular') or ''
    merged['nome_cientifico'] = merged.get('nome_cientifico') or new_item.get('nome_cientifico') or ''
    merged['nome_cientifico_valido'] = (
        merged.get('nome_cientifico_valido')
        or new_item.get('nome_cientifico_valido')
        or merged.get('nome_cientifico')
        or new_item.get('nome_cientifico')
        or ''
    )
    merged['familia'] = merged.get('familia') or new_item.get('familia') or ''
    merged['parte_comestivel'] = merged.get('parte_comestivel') or new_item.get('parte_comestivel') or ''
    merged['forma_uso'] = merged.get('forma_uso') or new_item.get('forma_uso') or ''
    merged['frutificacao'] = merged.get('frutificacao') or new_item.get('frutificacao') or new_item.get('epoca_frutificacao') or ''
    merged['colheita'] = merged.get('colheita') or new_item.get('colheita') or new_item.get('epoca_colheita') or ''
    merged['bioma'] = merged.get('bioma') or new_item.get('bioma') or ''
    merged['regiao'] = merged.get('regiao') or new_item.get('regiao') or new_item.get('regiao_ocorrencia') or ''
    merged['origem_integracao'] = merged.get('origem_integracao') or new_item.get('origem_integracao') or new_item.get('origem') or 'colaborapanc'
    merged['fonte_resultado'] = merged.get('fonte_resultado') or new_item.get('fonte_resultado') or 'referencial'
    merged['relevancia'] = max(int(merged.get('relevancia') or 0), int(new_item.get('relevancia') or 0))
    merged['score'] = max(float(merged.get('score') or 0), float(new_item.get('score') or 0))
    merged['ja_baixada'] = bool(merged.get('ja_baixada') or new_item.get('ja_baixada'))
    merged['tamanho_estimado_mb'] = float(merged.get('tamanho_estimado_mb') or new_item.get('tamanho_estimado_mb') or 0.5)
    merged['disponivel_para_offline'] = bool(merged.get('disponivel_para_offline') or new_item.get('disponivel_para_offline'))
    merged['nomes_populares'] = _merge_list_values(
        merged.get('nomes_populares') or [merged.get('nome_popular')],
        new_item.get('nomes_populares') or [new_item.get('nome_popular')]
    )
    merged['sinonimos'] = _merge_list_values(merged.get('sinonimos'), new_item.get('sinonimos'))
    fontes = _merge_list_values(
        merged.get('fontes_dados') or [merged.get('fonte_resultado')],
        new_item.get('fontes_dados') or [new_item.get('fonte_resultado')]
    )
    merged['fontes_dados'] = fontes
    return merged


def _consolidar_especies_resultados(resultados):
    mapa = {}
    for item in resultados:
        key = _species_dedupe_key(item)
        if not key:
            continue
        atual = mapa.get(key)
        if not atual:
            mapa[key] = _merge_species({}, item)
            continue
        prefer_new = (
            _fonte_score(item) > _fonte_score(atual)
            or (
                _fonte_score(item) == _fonte_score(atual)
                and _completeness_score(item) > _completeness_score(atual)
            )
        )
        mapa[key] = _merge_species(item if prefer_new else atual, atual if prefer_new else item)

    consolidadas = list(mapa.values())
    consolidadas.sort(key=lambda x: (x.get('relevancia', 0), _fonte_score(x), _completeness_score(x)), reverse=True)
    return consolidadas


def _build_referential_payload(planta, plantas_baixadas_set=None, relevancia=0):
    plantas_baixadas_set = plantas_baixadas_set or set()
    tem_modelo_ar = ModeloAR.objects.filter(planta=planta, ativo=True).exists()
    num_variacoes = PlantaCustomizada.objects.filter(
        planta_base=planta,
        validado_por_especialista=True
    ).count()
    tamanho_mb = 2.5 if tem_modelo_ar else 0.5
    stable_id = f"id:{planta.id}"
    return {
        'id': planta.id,
        'internal_id': planta.id,
        'external_id': None,
        'download_id': planta.id,
        'stable_id': stable_id,
        'plataforma_id': planta.id,
        'nome_popular': planta.nome_popular,
        'nome_cientifico': planta.nome_cientifico,
        'nome_cientifico_valido': planta.nome_cientifico_valido or planta.nome_cientifico or '',
        'nomes_populares': planta.nomes_populares or [planta.nome_popular],
        'sinonimos': planta.sinonimos or [],
        'aliases': planta.aliases or [],
        'familia': planta.familia or '',
        'grupo_taxonomico': planta.grupo_taxonomico or '',
        'bioma': planta.bioma or '',
        'regiao': planta.regiao_ocorrencia or '',
        'parte_comestivel': planta.parte_comestivel or '',
        'forma_uso': planta.forma_uso or '',
        'frutificacao': planta.epoca_frutificacao or '',
        'colheita': planta.epoca_colheita or '',
        'origem_integracao': planta.origem or 'colaborapanc',
        'fonte_resultado': 'referencial_interna',
        'fonte': planta.fonte or 'referencial_interna',
        'score': relevancia,
        'relevancia': relevancia,
        'ja_baixada': planta.id in plantas_baixadas_set,
        'tamanho_estimado_mb': round(tamanho_mb, 2),
        'tem_modelo_ar': tem_modelo_ar,
        'num_variacoes': num_variacoes,
        'disponivel_offline': planta.id in plantas_baixadas_set,
        'disponivel_para_offline': True,
    }


def _safe_dict(value):
    return value if isinstance(value, dict) else {}


def _hash_string(value):
    text = str(value or '')
    h = 0
    for ch in text:
        h = ((h << 5) - h) + ord(ch)
        h &= 0xFFFFFFFF
    return f"h{abs(h)}"


def _normalizar_item_recursivo(item):
    data = _safe_dict(item)
    internal_id = data.get('internal_id')
    external_id = data.get('external_id')
    if not external_id and not internal_id:
        nome_chave = data.get('nome_cientifico') or data.get('nome_popular') or ''
        external_id = f"nc:{_hash_string(_normalizar_texto(nome_chave))}" if nome_chave else None
    stable_id = data.get('stable_id') or (f"id:{internal_id}" if internal_id else external_id or f"payload:{_hash_string(json.dumps(data, ensure_ascii=False, sort_keys=True))}")
    download_id = data.get('download_id') or internal_id or external_id
    return {
        **data,
        'id': data.get('id') or internal_id or external_id or stable_id,
        'internal_id': internal_id,
        'external_id': external_id,
        'stable_id': stable_id,
        'download_id': download_id,
        'disponivel_para_offline': bool(download_id),
    }


# ===================================
# BUSCA CANÔNICA DE ESPÉCIES REFERENCIAIS
# ===================================
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def buscar_especies_referenciais(request):
    """
    Endpoint canônico para busca de espécies referenciais integradas.
    Busca em todos os campos relevantes com normalização e ranking.

    GET /api/especies-referenciais/busca/?q=termo&limite=50

    Retorna espécies da base referencial independente de pontos cadastrados.
    """
    try:
        termo = request.GET.get('q', '').strip()
        limite = min(int(request.GET.get('limite', 50)), 200)

        if not termo or len(termo) < 2:
            return Response({
                'sucesso': False,
                'erro': 'Termo de busca deve ter pelo menos 2 caracteres',
            }, status=status.HTTP_400_BAD_REQUEST)

        termo_normalizado = _normalizar_texto(termo)

        # Busca ampla: campos textuais diretos
        q_filter = (
            Q(nome_popular__icontains=termo) |
            Q(nome_cientifico__icontains=termo) |
            Q(nome_cientifico_valido__icontains=termo) |
            Q(nome_aceito__icontains=termo) |
            Q(familia__icontains=termo) |
            Q(genero__icontains=termo)
        )

        plantas_diretas = set(
            PlantaReferencial.objects.filter(q_filter).values_list('id', flat=True)
        )

        # Busca em JSONField (sinônimos, nomes_populares, aliases)
        # Para bancos que suportam, usamos icontains no JSONField serializado
        plantas_json = set()
        try:
            json_filter = (
                Q(sinonimos__icontains=termo) |
                Q(nomes_populares__icontains=termo) |
                Q(aliases__icontains=termo)
            )
            plantas_json = set(
                PlantaReferencial.objects.filter(json_filter).values_list('id', flat=True)
            )
        except Exception:
            # Fallback: busca em memória se o banco não suporta icontains em JSON
            pass

        # Busca normalizada (sem acentos) para capturar variações ortográficas
        plantas_normalizadas = set()
        if termo_normalizado != termo.lower():
            norm_filter = (
                Q(nome_popular__icontains=termo_normalizado) |
                Q(nome_cientifico__icontains=termo_normalizado)
            )
            plantas_normalizadas = set(
                PlantaReferencial.objects.filter(norm_filter).values_list('id', flat=True)
            )

        todos_ids = plantas_diretas | plantas_json | plantas_normalizadas

        if not todos_ids:
            return Response({
                'sucesso': True,
                'total': 0,
                'especies': [],
                'termo_buscado': termo,
            })

        plantas = PlantaReferencial.objects.filter(id__in=todos_ids)

        # Pega plantas já baixadas pelo usuário
        plantas_baixadas = set(
            PlantaOfflineUsuario.objects.filter(
                usuario=request.user,
                status='concluido'
            ).values_list('planta_id', flat=True)
        )

        # Monta resultado com ranking de relevância
        resultados = []
        for planta in plantas:
            relevancia = _calcular_relevancia(planta, termo_normalizado)
            if relevancia == 0:
                # Checagem em memória para JSONField que pode não ter sido capturado pelo icontains
                for np in (planta.nomes_populares or []):
                    if termo_normalizado in _normalizar_texto(np):
                        relevancia = 10
                        break
                if relevancia == 0:
                    for alias in (planta.aliases or []):
                        if termo_normalizado in _normalizar_texto(alias):
                            relevancia = 8
                            break
                if relevancia == 0:
                    for sin in (planta.sinonimos or []):
                        if termo_normalizado in _normalizar_texto(sin):
                            relevancia = 6
                            break
                if relevancia == 0:
                    relevancia = 1  # match básico pelo icontains do banco

            payload = _build_referential_payload(planta, plantas_baixadas, relevancia)
            payload.update({
                'status_enriquecimento': planta.status_enriquecimento or 'pendente',
                'nivel_confianca': float(planta.nivel_confianca_enriquecimento or 0.0),
                'tipo': 'referencial',
            })
            resultados.append(payload)

        # Ordena por relevância (maior primeiro)
        resultados.sort(key=lambda x: x['relevancia'], reverse=True)
        resultados = resultados[:limite]

        return Response({
            'sucesso': True,
            'total': len(resultados),
            'especies': resultados,
            'termo_buscado': termo,
        })

    except Exception as e:
        logger.error(f"Erro ao buscar espécies referenciais: {str(e)}")
        return Response({
            'sucesso': False,
            'erro': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def buscar_especies_referenciais_recursiva(request):
    """
    Busca recursiva/multifonte para descoberta de espécies referenciais:
    - Base referencial interna
    - Integrações (GBIF e iNaturalist via backend)
    - Expansão por nome científico/sinônimos/nomes populares
    """
    try:
        termo = request.GET.get('q', '').strip()
        filtros = request.GET.get('filtros', '')
        limite = min(int(request.GET.get('limite', 50)), 100)
        profundidade_max = min(int(request.GET.get('profundidade_max', 2)), 3)

        if not termo or len(termo) < 2:
            return Response({'sucesso': False, 'erro': 'Termo de busca deve ter pelo menos 2 caracteres'}, status=status.HTTP_400_BAD_REQUEST)

        termos_visitados = set()
        fila = [(termo, 0)]
        resultados = []

        plantas_baixadas = set(
            PlantaOfflineUsuario.objects.filter(
                usuario=request.user,
                status='concluido'
            ).values_list('planta_id', flat=True)
        )

        gbif = GBIFService()
        inat = INaturalistService()

        while fila and len(resultados) < limite:
            termo_atual, nivel = fila.pop(0)
            termo_norm = _normalizar_texto(termo_atual)
            if not termo_norm or termo_norm in termos_visitados:
                continue
            termos_visitados.add(termo_norm)

            q_filter = (
                Q(nome_popular__icontains=termo_atual) |
                Q(nome_cientifico__icontains=termo_atual) |
                Q(nome_cientifico_valido__icontains=termo_atual) |
                Q(nome_aceito__icontains=termo_atual) |
                Q(familia__icontains=termo_atual) |
                Q(nomes_populares__icontains=termo_atual) |
                Q(sinonimos__icontains=termo_atual)
            )
            internas = PlantaReferencial.objects.filter(q_filter)[:limite]
            for planta in internas:
                relevancia = _calcular_relevancia(planta, termo_norm)
                payload = _normalizar_item_recursivo(_build_referential_payload(planta, plantas_baixadas, relevancia))
                resultados.append(payload)
                if nivel < profundidade_max:
                    expansoes = []
                    if payload.get('nome_cientifico'):
                        expansoes.append(payload['nome_cientifico'])
                    expansoes.extend((payload.get('sinonimos') or [])[:3])
                    expansoes.extend((payload.get('nomes_populares') or [])[:2])
                    for termo_expandido in expansoes:
                        termo_expandido_norm = _normalizar_texto(termo_expandido)
                        if termo_expandido_norm and termo_expandido_norm not in termos_visitados:
                            fila.append((termo_expandido, nivel + 1))

            # Consulta integrações externas com termo atual
            integration_inputs = set()
            for item in resultados[-10:]:
                if item.get('nome_cientifico'):
                    integration_inputs.add(item['nome_cientifico'])
            integration_inputs.add(termo_atual)

            for sci_name in list(integration_inputs)[:5]:
                sci_name = (sci_name or '').strip()
                if len(sci_name) < 2:
                    continue

                try:
                    gbif_res = _safe_dict(gbif.fetch(sci_name))
                except Exception as integration_error:
                    logger.warning(f"Falha GBIF para '{sci_name}': {integration_error}")
                    gbif_res = {}
                if gbif_res.get('ok'):
                    external_id = f"nc:{_hash_string(_normalizar_texto(gbif_res.get('nome_cientifico_validado') or sci_name))}"
                    resultados.append(_normalizar_item_recursivo({
                        'id': external_id,
                        'internal_id': None,
                        'external_id': external_id,
                        'download_id': external_id,
                        'nome_popular': '',
                        'nome_cientifico': gbif_res.get('nome_cientifico_validado') or sci_name,
                        'nome_cientifico_valido': gbif_res.get('nome_cientifico_validado') or sci_name,
                        'nomes_populares': [],
                        'sinonimos': [],
                        'familia': '',
                        'parte_comestivel': '',
                        'forma_uso': '',
                        'frutificacao': '',
                        'colheita': '',
                        'bioma': gbif_res.get('distribuicao_resumida') or '',
                        'regiao': '',
                        'origem_integracao': 'gbif',
                        'fonte_resultado': 'integracao_gbif',
                        'score': 40 if _normalizar_texto(sci_name) == termo_norm else 20,
                        'relevancia': 40 if _normalizar_texto(sci_name) == termo_norm else 20,
                        'ja_baixada': False,
                        'tamanho_estimado_mb': 0.5,
                        'disponivel_offline': False,
                    }))

                try:
                    inat_res = _safe_dict(inat.fetch(sci_name))
                except Exception as integration_error:
                    logger.warning(f"Falha iNaturalist para '{sci_name}': {integration_error}")
                    inat_res = {}
                if inat_res.get('ok'):
                    external_id = f"nc:{_hash_string(_normalizar_texto(sci_name))}"
                    resultados.append(_normalizar_item_recursivo({
                        'id': external_id,
                        'internal_id': None,
                        'external_id': external_id,
                        'download_id': external_id,
                        'nome_popular': '',
                        'nome_cientifico': sci_name,
                        'nome_cientifico_valido': sci_name,
                        'nomes_populares': [],
                        'sinonimos': [],
                        'familia': '',
                        'parte_comestivel': '',
                        'forma_uso': '',
                        'frutificacao': inat_res.get('fenologia_observada') or '',
                        'colheita': '',
                        'bioma': '',
                        'regiao': '',
                        'origem_integracao': 'inaturalist',
                        'fonte_resultado': 'integracao_inaturalist',
                        'score': 30 if _normalizar_texto(sci_name) == termo_norm else 15,
                        'relevancia': 30 if _normalizar_texto(sci_name) == termo_norm else 15,
                        'ja_baixada': False,
                        'tamanho_estimado_mb': 0.5,
                        'disponivel_offline': False,
                    }))

            if nivel >= profundidade_max:
                continue

        consolidados = [_normalizar_item_recursivo(item) for item in _consolidar_especies_resultados(resultados)[:limite]]
        return Response({
            'sucesso': True,
            'total': len(consolidados),
            'especies': consolidados,
            'resultados': consolidados,
            'termo_buscado': termo,
            'profundidade_max': profundidade_max,
            'filtros': filtros,
            'fontes_consultadas': ['referencial_interna', 'integracao_gbif', 'integracao_inaturalist'],
        })
    except Exception as e:
        logger.error(f"Erro ao buscar espécies referenciais recursivamente: {str(e)}")
        return Response({'sucesso': False, 'erro': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ===================================
# LISTAGEM DE PLANTAS DISPONÍVEIS
# ===================================
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def listar_plantas_disponiveis(request):
    """
    Lista todas as plantas disponíveis para download offline

    Query params:
    - busca: filtrar por nome
    - bioma: filtrar por bioma
    - regiao: filtrar por região
    - grupo_taxonomico: filtrar por grupo taxonômico
    - apenas_populares: retornar apenas as mais identificadas
    """
    try:
        plantas = PlantaReferencial.objects.all()

        # Filtros
        busca = request.GET.get('busca', '').strip()
        if busca:
            q_busca = (
                Q(nome_popular__icontains=busca) |
                Q(nome_cientifico__icontains=busca) |
                Q(nome_cientifico_valido__icontains=busca) |
                Q(nome_aceito__icontains=busca) |
                Q(familia__icontains=busca)
            )
            try:
                q_busca = q_busca | (
                    Q(sinonimos__icontains=busca) |
                    Q(nomes_populares__icontains=busca) |
                    Q(aliases__icontains=busca)
                )
            except Exception:
                pass
            plantas = plantas.filter(q_busca)

        bioma = request.GET.get('bioma', '').strip()
        if bioma:
            plantas = plantas.filter(bioma__icontains=bioma)

        regiao = request.GET.get('regiao', '').strip()
        if regiao:
            plantas = plantas.filter(regiao_ocorrencia__icontains=regiao)

        grupo = request.GET.get('grupo_taxonomico', '').strip()
        if grupo:
            plantas = plantas.filter(grupo_taxonomico__icontains=grupo)

        apenas_populares = request.GET.get('apenas_populares') == 'true'
        if apenas_populares:
            # Ordena por número de identificações
            plantas = plantas.annotate(
                num_identificacoes=Count('identificacoes')
            ).filter(num_identificacoes__gt=0).order_by('-num_identificacoes')[:50]

        # Pega plantas já baixadas pelo usuário
        plantas_baixadas = PlantaOfflineUsuario.objects.filter(
            usuario=request.user,
            status='concluido'
        ).values_list('planta_id', flat=True)

        # Serializa os dados
        resultado = []
        for planta in plantas:
            # Calcula tamanho estimado (500KB base + modelos AR se houver)
            tamanho_mb = 0.5
            tem_modelo_ar = ModeloAR.objects.filter(planta=planta, ativo=True).exists()
            if tem_modelo_ar:
                tamanho_mb += 2.0  # Modelos AR ~2MB

            # Conta variações customizadas
            num_variacoes = PlantaCustomizada.objects.filter(
                planta_base=planta,
                validado_por_especialista=True
            ).count()

            resultado.append({
                'id': planta.id,
                'nome_popular': planta.nome_popular,
                'nome_cientifico': planta.nome_cientifico,
                'grupo_taxonomico': planta.grupo_taxonomico or '',
                'bioma': planta.bioma or '',
                'regiao_ocorrencia': planta.regiao_ocorrencia or '',
                'parte_comestivel': planta.parte_comestivel or '',
                'epoca_frutificacao': getattr(planta, 'epoca_frutificacao', '') or getattr(planta, 'frutificacao', '') or '',
                'epoca_colheita': getattr(planta, 'epoca_colheita', '') or getattr(planta, 'colheita', '') or '',
                'forma_uso': planta.forma_uso or '',
                'origem': planta.origem or '',
                'ja_baixada': planta.id in plantas_baixadas,
                'tamanho_estimado_mb': round(tamanho_mb, 2),
                'tem_modelo_ar': tem_modelo_ar,
                'num_variacoes': num_variacoes,
            })

        return Response({
            'sucesso': True,
            'total': len(resultado),
            'plantas': resultado
        })

    except Exception as e:
        logger.error(f"Erro ao listar plantas disponíveis: {str(e)}")
        return Response({
            'sucesso': False,
            'erro': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ===================================
# LISTAGEM DE PACOTES PRÉ-DEFINIDOS
# ===================================
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def listar_pacotes_offline(request):
    """
    Lista pacotes pré-definidos de plantas para download
    """
    try:
        pacotes = PacotePlantasOffline.objects.filter(ativo=True).prefetch_related('plantas')

        resultado = []
        for pacote in pacotes:
            # Verifica quantas plantas do pacote já foram baixadas
            plantas_ids = list(pacote.plantas.values_list('id', flat=True))
            plantas_baixadas = PlantaOfflineUsuario.objects.filter(
                usuario=request.user,
                planta_id__in=plantas_ids,
                status='concluido'
            ).count()

            resultado.append({
                'id': pacote.id,
                'nome': pacote.nome,
                'descricao': pacote.descricao,
                'icone': pacote.icone.url if pacote.icone else None,
                'bioma': pacote.bioma,
                'regiao': pacote.regiao,
                'dificuldade': pacote.dificuldade,
                'total_plantas': pacote.plantas.count(),
                'plantas_baixadas': plantas_baixadas,
                'tamanho_estimado_mb': pacote.tamanho_estimado,
                'completo': plantas_baixadas == pacote.plantas.count(),
            })

        return Response({
            'sucesso': True,
            'pacotes': resultado
        })

    except Exception as e:
        logger.error(f"Erro ao listar pacotes offline: {str(e)}")
        return Response({
            'sucesso': False,
            'erro': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ===================================
# BAIXAR PLANTAS SELECIONADAS
# ===================================
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def baixar_plantas_selecionadas(request):
    """
    Inicia o download de plantas selecionadas

    POST data:
    {
        "plantas_ids": [1, 2, 3],
        "incluir_modelos_ar": false,
        "qualidade_fotos": "media"
    }
    """
    try:
        plantas_ids = request.data.get('plantas_ids', [])
        itens_selecionados = request.data.get('itens_selecionados', [])
        incluir_modelos_ar = request.data.get('incluir_modelos_ar', False)
        qualidade = request.data.get('qualidade_fotos', 'media')

        if not plantas_ids:
            return Response({
                'sucesso': False,
                'erro': 'Nenhuma planta selecionada'
            }, status=status.HTTP_400_BAD_REQUEST)

        itens_por_download = {}
        if isinstance(itens_selecionados, list):
            for item in itens_selecionados:
                if not isinstance(item, dict):
                    continue
                key = str(item.get('download_id') or item.get('id') or item.get('stable_id') or '').strip()
                if key:
                    itens_por_download[key] = item

        def _is_int_like(value):
            try:
                int(str(value).strip())
                return True
            except Exception:
                return False

        def resolver_especie_para_offline(download_id):
            raw = str(download_id).strip()
            if not raw:
                return None

            # 1) interno numérico
            if _is_int_like(raw):
                return PlantaReferencial.objects.filter(id=int(raw)).first()

            # 2) externo/canônico + contexto da seleção
            contexto = itens_por_download.get(raw, {})
            internal_id = contexto.get('internal_id')
            if _is_int_like(internal_id):
                planta = PlantaReferencial.objects.filter(id=int(internal_id)).first()
                if planta:
                    return planta

            # 3) matching por nome científico / popular
            nome_cientifico = (contexto.get('nome_cientifico') or '').strip()
            nome_popular = (contexto.get('nome_popular') or '').strip()
            if nome_cientifico:
                planta = PlantaReferencial.objects.filter(nome_cientifico__iexact=nome_cientifico).first()
                if planta:
                    return planta
            if nome_popular:
                planta = PlantaReferencial.objects.filter(nome_popular__iexact=nome_popular).first()
                if planta:
                    return planta

            # 4) persistência mínima para espécie externa descoberta
            if nome_cientifico or nome_popular:
                nome_base = nome_popular or nome_cientifico
                return PlantaReferencial.objects.create(
                    nome_popular=nome_base,
                    nome_cientifico=nome_cientifico or nome_base,
                    nome_cientifico_valido=nome_cientifico or '',
                    parte_comestivel=contexto.get('parte_comestivel') or '',
                    epoca_frutificacao=contexto.get('epoca_frutificacao') or contexto.get('frutificacao') or '',
                    epoca_colheita=contexto.get('epoca_colheita') or contexto.get('colheita') or '',
                    forma_uso=contexto.get('forma_uso') or '',
                    grupo_taxonomico=contexto.get('grupo_taxonomico') or 'integracao_externa',
                    origem=contexto.get('origem_integracao') or 'integracao_externa',
                    bioma=contexto.get('bioma') or '',
                    regiao_ocorrencia=contexto.get('regiao') or contexto.get('regiao_ocorrencia') or '',
                    fonte=contexto.get('fonte_resultado') or 'integracao_externa',
                    sinonimos=contexto.get('sinonimos') or [],
                    nomes_populares=contexto.get('nomes_populares') or ([nome_popular] if nome_popular else []),
                )
            return None

        plantas = []
        itens_nao_resolvidos = []
        for download_id in plantas_ids:
            planta = resolver_especie_para_offline(download_id)
            if planta:
                plantas.append(planta)
            else:
                itens_nao_resolvidos.append(download_id)

        if not plantas:
            return Response({
                'sucesso': False,
                'erro': 'Nenhuma espécie pôde ser resolvida para download',
                'itens_nao_resolvidos': itens_nao_resolvidos,
            }, status=status.HTTP_400_BAD_REQUEST)

        # Cria ou atualiza registros de plantas offline
        plantas_criadas = []
        plantas_atualizadas = []

        for planta in plantas:
            planta_offline, criada = PlantaOfflineUsuario.objects.get_or_create(
                usuario=request.user,
                planta=planta,
                defaults={
                    'status': 'pendente',
                    'progresso': 0
                }
            )

            if not criada and planta_offline.status == 'concluido':
                # Atualizar planta existente
                planta_offline.status = 'pendente'
                planta_offline.progresso = 0
                planta_offline.save()
                plantas_atualizadas.append(planta.id)
            else:
                plantas_criadas.append(planta.id)

        # Atualiza configurações do usuário
        config, _ = ConfiguracaoOffline.objects.get_or_create(usuario=request.user)
        config.incluir_modelos_ar = incluir_modelos_ar
        config.qualidade_fotos = qualidade
        config.save()

        return Response({
            'sucesso': True,
            'mensagem': f'{len(plantas_criadas)} plantas adicionadas para download',
            'plantas_criadas': len(plantas_criadas),
            'plantas_atualizadas': len(plantas_atualizadas),
            'total': len(plantas_ids),
            'itens_nao_resolvidos': itens_nao_resolvidos,
        })

    except Exception as e:
        logger.error(f"Erro ao iniciar download de plantas: {str(e)}")
        return Response({
            'sucesso': False,
            'erro': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ===================================
# OBTER DADOS COMPLETOS DA PLANTA
# ===================================
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def obter_dados_planta(request, planta_id):
    """
    Retorna todos os dados de uma planta específica para armazenamento offline
    Inclui: dados básicos, variações customizadas, features para identificação
    """
    try:
        planta = PlantaReferencial.objects.get(id=planta_id)

        # Dados básicos da planta
        dados = {
            'id': planta.id,
            'nome_popular': planta.nome_popular,
            'nome_cientifico': planta.nome_cientifico,
            'nome_cientifico_valido': planta.nome_cientifico_valido or '',
            'parte_comestivel': planta.parte_comestivel or '',
            'epoca_frutificacao': getattr(planta, 'epoca_frutificacao', '') or getattr(planta, 'frutificacao', '') or '',
            'epoca_colheita': getattr(planta, 'epoca_colheita', '') or getattr(planta, 'colheita', '') or '',
            'forma_uso': planta.forma_uso or '',
            'grupo_taxonomico': planta.grupo_taxonomico or '',
            'origem': planta.origem or '',
            'bioma': planta.bioma or '',
            'regiao_ocorrencia': planta.regiao_ocorrencia or '',
            'fonte': planta.fonte or '',
        }

        # Variações customizadas validadas
        variacoes = PlantaCustomizada.objects.filter(
            planta_base=planta,
            validado_por_especialista=True
        )

        dados['variacoes'] = []
        for variacao in variacoes:
            var_data = {
                'id': variacao.id,
                'nome_variacao': variacao.nome_variacao,
                'descricao': variacao.descricao,
                'cor_folha': variacao.cor_folha or '',
                'formato_folha': variacao.formato_folha or '',
                'tamanho_medio': variacao.tamanho_medio or '',
                'textura': variacao.textura or '',
                'cor_flor': variacao.cor_flor or '',
                'epoca_floracao': variacao.epoca_floracao or '',
                'caracteristicas_especiais': variacao.caracteristicas_especiais or '',
                'regiao_encontrada': variacao.regiao_encontrada or '',
                'clima_predominante': variacao.clima_predominante or '',
                'features_ml': variacao.features_ml or {},
                'fotos': {
                    'folha': variacao.foto_folha.url if variacao.foto_folha else None,
                    'flor': variacao.foto_flor.url if variacao.foto_flor else None,
                    'fruto': variacao.foto_fruto.url if variacao.foto_fruto else None,
                    'planta_inteira': variacao.foto_planta_inteira.url if variacao.foto_planta_inteira else None,
                }
            }
            dados['variacoes'].append(var_data)

        # Modelos AR disponíveis
        incluir_ar = request.GET.get('incluir_ar') == 'true'
        if incluir_ar:
            modelos_ar = ModeloAR.objects.filter(planta=planta, ativo=True)
            dados['modelos_ar'] = []
            for modelo in modelos_ar:
                dados['modelos_ar'].append({
                    'id': modelo.id,
                    'nome': modelo.nome,
                    'url_modelo': modelo.modelo_glb.url if modelo.modelo_glb else None,
                    'preview': modelo.preview_image.url if modelo.preview_image else None,
                    'escala_padrao': modelo.escala_padrao,
                    'formato': modelo.formato,
                    'tamanho_mb': round(modelo.tamanho_arquivo / (1024 * 1024), 2) if modelo.tamanho_arquivo else 0,
                })
        else:
            dados['modelos_ar'] = []

        # Calcula tamanho total estimado
        tamanho_mb = 0.5  # Base
        tamanho_mb += len(variacoes) * 0.3  # Cada variação ~300KB
        if incluir_ar:
            tamanho_mb += sum(m.tamanho_arquivo / (1024 * 1024) for m in modelos_ar if m.tamanho_arquivo)

        dados['tamanho_total_mb'] = round(tamanho_mb, 2)
        dados['versao'] = timezone.now().strftime('%Y%m%d%H%M%S')

        # Atualiza o registro de planta offline
        planta_offline, _ = PlantaOfflineUsuario.objects.get_or_create(
            usuario=request.user,
            planta=planta
        )
        planta_offline.dados_completos = dados
        planta_offline.tamanho_total_mb = tamanho_mb
        planta_offline.versao_dados = dados['versao']
        planta_offline.ultima_atualizacao = timezone.now()
        planta_offline.status = 'concluido'
        planta_offline.progresso = 100
        planta_offline.save()

        # Atualiza configuração do usuário
        config, _ = ConfiguracaoOffline.objects.get_or_create(usuario=request.user)
        config.atualizar_estatisticas()

        return Response({
            'sucesso': True,
            'dados': dados
        })

    except PlantaReferencial.DoesNotExist:
        return Response({
            'sucesso': False,
            'erro': 'Planta não encontrada'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Erro ao obter dados da planta {planta_id}: {str(e)}")
        return Response({
            'sucesso': False,
            'erro': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ===================================
# LISTAR PLANTAS BAIXADAS DO USUÁRIO
# ===================================
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def listar_plantas_baixadas(request):
    """
    Lista todas as plantas já baixadas pelo usuário
    """
    try:
        plantas_offline = PlantaOfflineUsuario.objects.filter(
            usuario=request.user
        ).select_related('planta').order_by('-atualizado_em')

        resultado = []
        for planta_offline in plantas_offline:
            resultado.append({
                'id': planta_offline.id,
                'planta_id': planta_offline.planta.id,
                'nome_popular': planta_offline.planta.nome_popular,
                'nome_cientifico': planta_offline.planta.nome_cientifico,
                'status': planta_offline.status,
                'progresso': planta_offline.progresso,
                'tamanho_mb': planta_offline.tamanho_total_mb,
                'modelo_ar_baixado': planta_offline.modelo_ar_baixado,
                'vezes_identificada': planta_offline.vezes_identificada,
                'ultima_identificacao': planta_offline.ultima_identificacao.isoformat() if planta_offline.ultima_identificacao else None,
                'ultima_atualizacao': planta_offline.ultima_atualizacao.isoformat() if planta_offline.ultima_atualizacao else None,
                'versao_dados': planta_offline.versao_dados,
            })

        # Estatísticas gerais
        config, _ = ConfiguracaoOffline.objects.get_or_create(usuario=request.user)
        config.atualizar_estatisticas()

        return Response({
            'sucesso': True,
            'plantas': resultado,
            'estatisticas': {
                'total_plantas': config.total_plantas_baixadas,
                'espaco_usado_mb': round(config.espaco_usado_mb, 2),
                'limite_mb': config.limite_armazenamento_mb,
                'percentual_usado': round((config.espaco_usado_mb / config.limite_armazenamento_mb) * 100, 1) if config.limite_armazenamento_mb > 0 else 0,
            }
        })

    except Exception as e:
        logger.error(f"Erro ao listar plantas baixadas: {str(e)}")
        return Response({
            'sucesso': False,
            'erro': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ===================================
# REMOVER PLANTA OFFLINE
# ===================================
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def remover_planta_offline(request, planta_id):
    """
    Remove uma planta dos dados offline do usuário
    """
    try:
        planta_offline = PlantaOfflineUsuario.objects.get(
            usuario=request.user,
            planta_id=planta_id
        )

        nome_planta = planta_offline.planta.nome_popular
        planta_offline.delete()

        # Atualiza estatísticas
        config, _ = ConfiguracaoOffline.objects.get_or_create(usuario=request.user)
        config.atualizar_estatisticas()

        return Response({
            'sucesso': True,
            'mensagem': f'Planta "{nome_planta}" removida com sucesso'
        })

    except PlantaOfflineUsuario.DoesNotExist:
        return Response({
            'sucesso': False,
            'erro': 'Planta offline não encontrada'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Erro ao remover planta offline: {str(e)}")
        return Response({
            'sucesso': False,
            'erro': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ===================================
# CONFIGURAÇÕES OFFLINE DO USUÁRIO
# ===================================
@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def configuracoes_offline(request):
    """
    GET: Retorna configurações offline do usuário
    PUT: Atualiza configurações offline do usuário
    """
    try:
        config, _ = ConfiguracaoOffline.objects.get_or_create(usuario=request.user)

        if request.method == 'GET':
            return Response({
                'sucesso': True,
                'configuracoes': {
                    'baixar_apenas_wifi': config.baixar_apenas_wifi,
                    'qualidade_fotos': config.qualidade_fotos,
                    'incluir_modelos_ar': config.incluir_modelos_ar,
                    'limite_armazenamento_mb': config.limite_armazenamento_mb,
                    'auto_limpar_antigas': config.auto_limpar_antigas,
                    'auto_atualizar': config.auto_atualizar,
                    'frequencia_atualizacao': config.frequencia_atualizacao,
                    'espaco_usado_mb': round(config.espaco_usado_mb, 2),
                    'total_plantas_baixadas': config.total_plantas_baixadas,
                    'ultima_sincronizacao': config.ultima_sincronizacao.isoformat() if config.ultima_sincronizacao else None,
                }
            })

        elif request.method == 'PUT':
            # Atualiza configurações
            if 'baixar_apenas_wifi' in request.data:
                config.baixar_apenas_wifi = request.data['baixar_apenas_wifi']
            if 'qualidade_fotos' in request.data:
                config.qualidade_fotos = request.data['qualidade_fotos']
            if 'incluir_modelos_ar' in request.data:
                config.incluir_modelos_ar = request.data['incluir_modelos_ar']
            if 'limite_armazenamento_mb' in request.data:
                config.limite_armazenamento_mb = request.data['limite_armazenamento_mb']
            if 'auto_limpar_antigas' in request.data:
                config.auto_limpar_antigas = request.data['auto_limpar_antigas']
            if 'auto_atualizar' in request.data:
                config.auto_atualizar = request.data['auto_atualizar']
            if 'frequencia_atualizacao' in request.data:
                config.frequencia_atualizacao = request.data['frequencia_atualizacao']

            config.save()

            return Response({
                'sucesso': True,
                'mensagem': 'Configurações atualizadas com sucesso'
            })

    except Exception as e:
        logger.error(f"Erro ao gerenciar configurações offline: {str(e)}")
        return Response({
            'sucesso': False,
            'erro': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ===================================
# BAIXAR PACOTE COMPLETO
# ===================================
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def baixar_pacote(request, pacote_id):
    """
    Baixa todas as plantas de um pacote pré-definido
    """
    try:
        pacote = PacotePlantasOffline.objects.get(id=pacote_id, ativo=True)
        plantas = list(pacote.plantas.all())

        if not plantas:
            return Response({
                'sucesso': False,
                'erro': 'Pacote vazio'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Cria registros para todas as plantas do pacote
        plantas_criadas = 0
        plantas_existentes = 0

        for planta in plantas:
            _, criada = PlantaOfflineUsuario.objects.get_or_create(
                usuario=request.user,
                planta=planta,
                defaults={
                    'status': 'pendente',
                    'progresso': 0
                }
            )
            if criada:
                plantas_criadas += 1
            else:
                plantas_existentes += 1

        return Response({
            'sucesso': True,
            'mensagem': f'Pacote "{pacote.nome}" adicionado para download',
            'total_plantas': len(plantas),
            'plantas_novas': plantas_criadas,
            'plantas_existentes': plantas_existentes,
        })

    except PacotePlantasOffline.DoesNotExist:
        return Response({
            'sucesso': False,
            'erro': 'Pacote não encontrado'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Erro ao baixar pacote: {str(e)}")
        return Response({
            'sucesso': False,
            'erro': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ===================================
# SINCRONIZAR STATUS DE DOWNLOAD
# ===================================
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def sincronizar_status(request):
    """
    Sincroniza o status de download de múltiplas plantas

    POST data:
    {
        "plantas": [
            {"planta_id": 1, "status": "concluido", "progresso": 100},
            {"planta_id": 2, "status": "baixando", "progresso": 45}
        ]
    }
    """
    try:
        plantas_data = request.data.get('plantas', [])

        atualizadas = 0
        for planta_data in plantas_data:
            planta_id = planta_data.get('planta_id')
            novo_status = planta_data.get('status')
            progresso = planta_data.get('progresso', 0)

            try:
                planta_offline = PlantaOfflineUsuario.objects.get(
                    usuario=request.user,
                    planta_id=planta_id
                )
                planta_offline.status = novo_status
                planta_offline.progresso = progresso
                if novo_status == 'concluido':
                    planta_offline.ultima_atualizacao = timezone.now()
                planta_offline.save()
                atualizadas += 1
            except PlantaOfflineUsuario.DoesNotExist:
                logger.warning(f"Planta offline {planta_id} não encontrada para o usuário {request.user.id}")

        # Atualiza estatísticas
        config, _ = ConfiguracaoOffline.objects.get_or_create(usuario=request.user)
        config.ultima_sincronizacao = timezone.now()
        config.atualizar_estatisticas()
        config.save()

        return Response({
            'sucesso': True,
            'plantas_atualizadas': atualizadas
        })

    except Exception as e:
        logger.error(f"Erro ao sincronizar status: {str(e)}")
        return Response({
            'sucesso': False,
            'erro': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
