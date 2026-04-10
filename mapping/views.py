# ========================================
# IMPORTS
# ========================================
from rest_framework import viewsets, serializers, generics, status
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.core.cache import cache
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User, Group
from django.db.models import Count, Sum, Q, Prefetch
from django.db import IntegrityError, transaction
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from django.contrib.auth import authenticate, login as django_login
from rest_framework.decorators import api_view, authentication_classes, permission_classes, action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authtoken.models import Token
import csv
import json
import requests
import calendar
import logging
from typing import Any
from datetime import datetime, timedelta
from .models import (
    Missao, Badge, MissaoUsuario, HistoricoGamificacao, PontuacaoUsuario, SugestaoMissao,
    BotaoFlutuante, RankingRevisor,
    PontoPANC, PlantaReferencial, ParecerValidacao,
    Grupo, Feedback, UsuarioBadge, DispositivoPush, Notificacao,
    Conversa, Mensagem, CompartilhamentoSocial, RecomendacaoPANC,
    IntegracaoEcommerce, ProdutoSemente, RoteiroPANC, RoteiroPANCItem,
    ReferenciaAR, AlertaClimatico, EventoMonitorado, TIPOS_DE_LOCAL
)
from .forms import PontoPANCForm, SugestaoMissaoForm
from .identificacao_api import identificar_planta_api
from .services.plant_identification_service import PlantIdentificationService
from .services.enrichment_orchestrator import EnrichmentOrchestrator
from .services.enrichment.planta_enrichment_pipeline import PlantaEnrichmentPipeline
from .services.enrichment.canonical_store import CanonicalPlantStore
from .utils import adicionar_pontos, pontos_disponiveis_para_criador, registrar_acao_gamificada
from .utils.cache_keys import build_safe_cache_key
from .serializers import (
    AlertaClimaticoSerializer, PontoPANCSerializer, DispositivoPushSerializer,
    NotificacaoSerializer, ConversaSerializer, MensagemSerializer,
    CompartilhamentoSocialSerializer, RecomendacaoPANCSerializer,
    IntegracaoEcommerceSerializer, ProdutoSementeSerializer, RoteiroPANCSerializer,
    RoteiroPANCItemSerializer, ReferenciaARSerializer
)
from .services.rotas_service import rotas_service
from .services.integration_health import IntegrationHealthService
from .services.mobile_parity_service import MobileParityService

logger = logging.getLogger(__name__)
plant_identification_service = PlantIdentificationService()
enrichment_orchestrator = EnrichmentOrchestrator()
plant_enrichment_pipeline = PlantaEnrichmentPipeline()
canonical_store = CanonicalPlantStore()
integration_health_service = IntegrationHealthService()
mobile_parity_service = MobileParityService()

# =======================
# DECORATORS DE PERMISSÃO
# =======================

def admin_required(view_func):
    return user_passes_test(lambda u: u.is_superuser)(view_func)

def revisor_required(view_func):
    return user_passes_test(lambda u: u.is_authenticated and (u.is_superuser or u.groups.filter(name="Revisores").exists()))(view_func)

# =======================
# UTILITÁRIOS GERAIS
# =======================

def buscar_cientifico(nome_popular):
    """Busca nome científico a partir do nome popular."""
    planta = PlantaReferencial.objects.filter(nome_popular__iexact=nome_popular.strip()).first()
    return planta.nome_cientifico if planta else ''

def is_revisor(user):
    """Checa se o usuário é do grupo de Revisores ou admin."""
    return user.is_authenticated and (user.is_superuser or user.groups.filter(name='Revisores').exists())

def is_admin_user(user):
    return user.is_authenticated and (user.is_superuser or user.is_staff)


def _montar_sugestoes_nomes_populares(termo: str, limite: int = 10) -> list[dict]:
    """Monta sugestões priorizando base local e usando fallback externo opcional."""
    termo = (termo or "").strip()
    if len(termo) < 2:
        return []

    sugestoes: list[dict] = []
    seen: set[tuple[str, str]] = set()

    def add(nome_popular: str, nome_cientifico: str = "", source: str = "base_local", confianca: float = 0.0):
        popular = (nome_popular or "").strip()
        cientifico = (nome_cientifico or "").strip()
        if not popular:
            return
        key = (popular.lower(), cientifico.lower())
        if key in seen:
            return
        seen.add(key)
        sugestoes.append(
            {
                "nome_popular": popular,
                "nome_cientifico": cientifico,
                "source": source,
                "confianca": confianca,
            }
        )

    locais_validados = PlantaReferencial.objects.filter(
        Q(nome_popular__istartswith=termo) | Q(nome_popular__icontains=termo)
    ).order_by("nome_popular")[: limite * 2]
    for planta in locais_validados:
        score = 1.0 if planta.nome_cientifico else 0.85
        add(planta.nome_popular, planta.nome_cientifico, "base_local_validada", score)

    pontos_existentes = (
        PontoPANC.objects.filter(nome_popular__icontains=termo)
        .exclude(nome_popular="")
        .values_list("nome_popular", flat=True)
        .distinct()[:limite]
    )
    for nome_popular in pontos_existentes:
        if len(sugestoes) >= limite:
            break
        add(nome_popular, "", "historico_pontos", 0.6)

    if len(sugestoes) < limite:
        cache_key = build_safe_cache_key("autocomplete-inat", termo)
        cached = cache.get(cache_key)
        if cached is None:
            try:
                response = requests.get(
                    "https://api.inaturalist.org/v1/taxa/autocomplete",
                    params={"q": termo, "locale": "pt-BR", "per_page": 6},
                    timeout=3,
                    headers={"User-Agent": "ColaboraPANC/1.0 (+https://foodlens.com.br)"},
                )
                response.raise_for_status()
                payload = response.json()
                cached = payload.get("results", []) if isinstance(payload, dict) else []
            except Exception as exc:
                logger.info("Fallback externo do autocomplete indisponível (%s): %s", termo, exc)
                cached = []
            cache.set(cache_key, cached, 60 * 20)

        for item in cached:
            if len(sugestoes) >= limite:
                break
            taxon = item.get("matched_term") or item.get("preferred_common_name") or ""
            nome_cientifico = item.get("name") or ""
            add(taxon, nome_cientifico, "inaturalist", 0.5)

    sugestoes.sort(key=lambda x: x.get("confianca", 0), reverse=True)
    return sugestoes[:limite]


def _resolver_nome_cientifico_por_sugestao(nome_popular: str) -> dict:
    nome = (nome_popular or "").strip()
    if not nome:
        return {"nome_cientifico": "", "source": "none", "resolved": False}

    planta = PlantaReferencial.objects.filter(nome_popular__iexact=nome).first()
    if planta and planta.nome_cientifico:
        return {
            "nome_cientifico": planta.nome_cientifico,
            "source": "base_local_validada",
            "resolved": True,
        }

    sugestoes = _montar_sugestoes_nomes_populares(nome, limite=5)
    for item in sugestoes:
        if item["nome_popular"].strip().lower() == nome.lower() and item.get("nome_cientifico"):
            return {
                "nome_cientifico": item["nome_cientifico"],
                "source": item["source"],
                "resolved": True,
            }

    return {"nome_cientifico": "", "source": "none", "resolved": False}


def _split_csv_field(value: str) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in str(value).split(",") if item and item.strip()]


def _apply_manual_food_fields_to_ponto(ponto: PontoPANC, *, payload: dict[str, Any]) -> None:
    comestibilidade_status = (payload.get("comestibilidade_status") or "indeterminado").strip().lower()
    if comestibilidade_status not in {"sim", "nao", "indeterminado"}:
        comestibilidade_status = "indeterminado"

    parte = _split_csv_field(payload.get("parte_comestivel_manual") or payload.get("parte_comestivel") or "")
    frutificacao = _split_csv_field(payload.get("frutificacao_manual") or payload.get("frutificacao_meses") or payload.get("epoca_frutificacao") or "")
    colheita_raw = payload.get("colheita_manual") or payload.get("colheita_periodo") or payload.get("epoca_colheita") or ""
    colheita = _split_csv_field(colheita_raw) if isinstance(colheita_raw, str) else colheita_raw

    if comestibilidade_status != "indeterminado":
        ponto.comestibilidade_status = comestibilidade_status
        ponto.comestibilidade_confirmada = True
    if parte:
        ponto.parte_comestivel_lista = parte
        ponto.parte_comestivel_confirmada = True
    if frutificacao:
        ponto.frutificacao_meses = frutificacao
        ponto.frutificacao_confirmada = True
    if colheita:
        ponto.colheita_periodo = colheita
        ponto.colheita_confirmada = True


def _sync_manual_fields_to_planta(ponto: PontoPANC) -> None:
    if not ponto.planta_id:
        return
    planta = ponto.planta
    updated = []
    if ponto.comestibilidade_confirmada:
        planta.comestivel = True if ponto.comestibilidade_status == "sim" else (False if ponto.comestibilidade_status == "nao" else None)
        updated.append("comestivel")
    if ponto.parte_comestivel_confirmada:
        planta.parte_comestivel = ", ".join(ponto.parte_comestivel_lista or [])
        updated.append("parte_comestivel")
    if ponto.frutificacao_confirmada:
        planta.epoca_frutificacao = ", ".join(ponto.frutificacao_meses or [])
        updated.append("epoca_frutificacao")
    if ponto.colheita_confirmada:
        planta.epoca_colheita = ", ".join(ponto.colheita_periodo) if isinstance(ponto.colheita_periodo, list) else str(ponto.colheita_periodo)
        updated.append("epoca_colheita")
    if updated:
        planta.save(update_fields=list(set(updated)))

@login_required
def painel_integracoes(request):
    if not is_admin_user(request.user):
        return HttpResponse(status=403)
    status_integracoes = None
    if request.method == "POST":
        nome = request.POST.get("integration_name")
        status_integracoes = integration_health_service.run(only_name=nome or None)

    if status_integracoes is None:
        status_integracoes = integration_health_service.check_all()
    resumo = {
        "online": sum(1 for item in status_integracoes if item["status"] == "online"),
        "degradada": sum(1 for item in status_integracoes if item["status"] == "degradada"),
        "offline": sum(1 for item in status_integracoes if item["status"] == "offline"),
    }
    return render(request, "mapping/painel_integracoes.html", {"integracoes": status_integracoes, "resumo": resumo})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def api_health_integracoes(request):
    if not is_admin_user(request.user):
        return Response({"detail": "forbidden"}, status=status.HTTP_403_FORBIDDEN)
    return Response({"integracoes": integration_health_service.check_all()})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def api_testar_integracoes(request):
    if not is_admin_user(request.user):
        return Response({"detail": "forbidden"}, status=status.HTTP_403_FORBIDDEN)

    nome = (request.data.get("integration_name") or "").strip() or None
    if nome:
        nomes_validos = {probe.nome for probe in integration_health_service.probes()}
        if nome not in nomes_validos:
            return Response(
                {
                    "detail": "integration_name inválido",
                    "integration_name": nome,
                    "valid_options": sorted(nomes_validos),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

    resultados = integration_health_service.run(only_name=nome or None)
    payload = []
    for item in resultados:
        payload.append(
            {
                "nome": item.get("nome"),
                "tipo_integracao": item.get("tipo_integracao"),
                "sucesso": item.get("sucesso", False),
                "status": item.get("status"),
                "status_detalhado": item.get("status_detalhado"),
                "tempo_resposta_ms": item.get("tempo_resposta_ms"),
                "error_type": item.get("error_type", "nenhum"),
                "mensagem_amigavel": item.get("mensagem_amigavel"),
                "mensagem_tecnica": item.get("mensagem_tecnica"),
                "configurada": item.get("configurada", False),
                "operacional": item.get("operacional", False),
                "variaveis_esperadas": item.get("variaveis_esperadas", []),
                "env_vars_ausentes": item.get("env_vars_ausentes", []),
                "ultima_verificacao": item.get("ultima_verificacao"),
                "ultimo_teste_bem_sucedido": item.get("ultimo_teste_bem_sucedido"),
                "ultima_falha_em": item.get("ultima_falha_em"),
                "ultimo_tipo_problema": item.get("ultimo_tipo_problema"),
                "latencia_nivel": item.get("latencia_nivel"),
                "resposta_resumida": item.get("resposta_resumida"),
            }
        )

    return Response(
        {
            "executado_em": timezone.now(),
            "total": len(payload),
            "resultados": payload,
        },
        status=status.HTTP_200_OK,
    )


def aplicar_filtros_pontos(request, queryset):
    nome = request.GET.get("nome")
    cidade = request.GET.get("cidade")
    estado = request.GET.get("estado")
    tipo_local = request.GET.get("tipo_local")
    status_validacao = request.GET.get("status_validacao")
    status_identificacao = request.GET.get("status_identificacao")
    grupo_id = request.GET.get("grupo")
    planta_id = request.GET.get("planta")
    criado_de = request.GET.get("criado_de")
    criado_ate = request.GET.get("criado_ate")
    lat = request.GET.get("lat")
    lng = request.GET.get("lng")
    raio_km = request.GET.get("raio_km")

    if nome:
        queryset = queryset.filter(
            Q(planta__nome_popular__icontains=nome)
            | Q(planta__nome_cientifico__icontains=nome)
            | Q(nome_popular__icontains=nome)
            | Q(nome_popular_sugerido__icontains=nome)
        )
    if cidade:
        queryset = queryset.filter(cidade__icontains=cidade)
    if estado:
        queryset = queryset.filter(estado__icontains=estado)
    if tipo_local:
        queryset = queryset.filter(tipo_local=tipo_local)
    if status_validacao:
        queryset = queryset.filter(status_validacao=status_validacao)
    if status_identificacao:
        queryset = queryset.filter(status_identificacao=status_identificacao)
    if grupo_id:
        queryset = queryset.filter(grupo_id=grupo_id)
    if planta_id:
        queryset = queryset.filter(planta_id=planta_id)
    if criado_de:
        queryset = queryset.filter(criado_em__date__gte=criado_de)
    if criado_ate:
        queryset = queryset.filter(criado_em__date__lte=criado_ate)
    if lat and lng and raio_km:
        try:
            ponto = Point(float(lng), float(lat), srid=4326)
            queryset = queryset.filter(localizacao__distance_lte=(ponto, D(km=float(raio_km))))
        except ValueError:
            pass

    return queryset


def serializar_ponto_api(ponto):
    if not ponto.localizacao:
        return None

    now = timezone.now()
    alertas = getattr(ponto, "alertas_ordenados", None)
    if alertas is None:
        alertas = ponto.alertas.filter(inicio__lte=now, fim__gte=now).order_by("-inicio")[:3]
    else:
        alertas = [a for a in alertas if a.inicio <= now <= a.fim][:3]
    eventos = getattr(ponto, "eventos_monitorados_ordenados", None)
    if eventos is None:
        eventos = ponto.eventos_monitorados.order_by("-ocorrido_em")[:3]
    else:
        eventos = eventos[:3]

    alertas_serializados = AlertaClimaticoSerializer(alertas, many=True).data
    for evento in eventos:
        alertas_serializados.append({
            "tipo": evento.get_tipo_evento_display(),
            "descricao": evento.descricao,
            "severidade": evento.severidade,
            "inicio": evento.ocorrido_em,
            "fim": evento.publicado_em or evento.ocorrido_em,
            "fonte": evento.fonte,
            "municipio": ponto.cidade or "",
            "uf": ponto.estado or "",
            "id_alerta": evento.external_id or evento.hash_evento,
            "icone": None,
            "distancia_metros": evento.distancia_metros,
            "confianca": evento.confianca,
            "tipo_evento": evento.tipo_evento,
        })
    seen = set()
    dedup = []
    for item in alertas_serializados:
        key = (item.get("fonte"), item.get("id_alerta"), item.get("tipo"), str(item.get("inicio")), str(item.get("fim")))
        if key in seen:
            continue
        seen.add(key)
        dedup.append(item)
    alertas_serializados = sorted(dedup, key=lambda item: item.get("inicio") or "", reverse=True)[:6]

    return {
        "id": ponto.id,
        "nome_popular": (
            ponto.planta.nome_popular if ponto.planta and ponto.planta.nome_popular
            else ponto.nome_popular_sugerido or ""
        ),
        "nome_cientifico": (
            ponto.planta.nome_cientifico if ponto.planta and ponto.planta.nome_cientifico
            else ponto.nome_cientifico_sugerido or ""
        ),
        "tipo_local": ponto.tipo_local or "",
        "colaborador": ponto.colaborador or "",
        "grupo": ponto.grupo.nome if ponto.grupo else "",
        "relato": ponto.relato or "",
        "foto_url": ponto.foto.url if ponto.foto else "",
        "status_validacao": ponto.status_validacao,
        "localizacao": [ponto.localizacao.x, ponto.localizacao.y],
        "alertas": alertas_serializados,
        "cidade": ponto.cidade or "",
        "estado": ponto.estado or "",
    }

# =======================
# VIEWS PÚBLICAS — MAPA, DETALHE E API DE PONTOS
# =======================

def mapa(request):
    """
    Exibe o mapa público (acessível a visitantes, usuários logados, revisores e admin).
    Adiciona variáveis de contexto para filtros e exibição especial para revisores.
    """
    pontos = PontoPANC.objects.select_related('planta', 'grupo').all()
    cidades = PontoPANC.objects.values_list('cidade', flat=True).distinct()
    estados = PontoPANC.objects.values_list('estado', flat=True).distinct()
    grupos = Grupo.objects.all()
    # Flag para exibir funções extras no mapa para revisor/admin
    is_revisor_flag = False
    if request.user.is_authenticated:
        is_revisor_flag = (
            request.user.is_superuser or 
            request.user.groups.filter(name='Revisores').exists()
        )
    return render(request, 'mapping/mapa.html', {
        'pontos': pontos,
        'cidades': cidades,
        'estados': estados,
        'grupos': grupos,
        'is_revisor': is_revisor_flag,
    })

def detalhe_ponto(request, pk):
    """
    Página de detalhes do ponto individual (acessível a qualquer usuário, inclusive visitante).
    """
    ponto = get_object_or_404(PontoPANC, pk=pk)
    can_edit_ponto = request.user.is_authenticated and (
        request.user.is_superuser or ponto.criado_por_id == request.user.id or ponto.colaborador == request.user.username
    )
    enriquecimento = None
    historico_enriquecimento = []
    if ponto.planta:
        planta = ponto.planta
        if planta.status_enriquecimento and planta.status_enriquecimento != 'pendente':
            enriquecimento = planta
        historico_enriquecimento = list(
            planta.historico_enriquecimento.order_by('-data')[:5].values('data', 'status', 'fontes_consultadas')
        )
    return render(request, 'mapping/detalhe_ponto.html', {
        'ponto': ponto,
        'can_edit_ponto': can_edit_ponto,
        'enriquecimento': enriquecimento,
        'historico_enriquecimento': historico_enriquecimento,
    })


@api_view(['GET'])
def api_pontos(request):
    try:
        pontos = (
            PontoPANC.objects
            .select_related('planta', 'grupo')
            .prefetch_related(
                Prefetch(
                    "alertas",
                    queryset=AlertaClimatico.objects.order_by("-inicio"),
                    to_attr="alertas_ordenados",
                ),
                Prefetch(
                    "eventos_monitorados",
                    queryset=EventoMonitorado.objects.order_by("-ocorrido_em"),
                    to_attr="eventos_monitorados_ordenados",
                ),
            )
            .filter(localizacao__isnull=False)
        )
        pontos = aplicar_filtros_pontos(request, pontos)
        serializer = PontoPANCSerializer(pontos, many=True, context={'request': request})
        return Response(serializer.data)
    except Exception:
        logger.exception("Erro em /api/pontos")
        return JsonResponse({"erro": "Erro interno."}, status=500)


# =======================
# CADASTRO / EDIÇÃO / REMOÇÃO
# =======================

@login_required
def painel_contribuicoes(request):
    pontos = PontoPANC.objects.filter(colaborador=request.user.username)
    return render(request, 'mapping/painel_contribuicoes.html', {'pontos': pontos})


@login_required
def cadastrar_ponto(request):
    identificacao_preview = None
    if request.method == 'POST':
        form = PontoPANCForm(request.POST, request.FILES)
        if form.is_valid():
            ponto = form.save(commit=False)
            ponto.criado_por = request.user
            ponto.colaborador = request.user.username
            ponto.cidade = request.POST.get('cidade', '').strip()
            ponto.estado = request.POST.get('estado', '').strip()
            ponto.bairro = request.POST.get('bairro', '').strip()
            ponto.endereco = request.POST.get('endereco', '').strip()
            ponto.numero = request.POST.get('numero', '').strip()
            ponto.status_validacao = 'pendente'

            nome_popular = (form.cleaned_data.get("nome_popular") or "").strip()
            nome_cientifico = (form.cleaned_data.get("nome_cientifico") or "").strip()
            foto = form.cleaned_data.get("foto")
            lat = ponto.localizacao.y if ponto.localizacao else None
            lon = ponto.localizacao.x if ponto.localizacao else None

            identificacao = plant_identification_service.identify(
                foto=foto,
                nome_popular=nome_popular,
                nome_cientifico=nome_cientifico,
                lat=lat,
                lon=lon,
            )
            identificacao_preview = {
                "nome_popular": identificacao.nome_popular,
                "nome_cientifico": identificacao.nome_cientifico,
                "score": identificacao.score,
                "fonte": identificacao.fonte,
            }
            planta, detalhe_resolucao = plant_identification_service.resolve_or_create_planta(
                nome_popular=nome_popular,
                nome_cientifico=nome_cientifico,
                identification=identificacao,
            )
            if not planta:
                form.add_error(
                    "nome_popular",
                    detalhe_resolucao,
                )
            else:
                ponto.planta = planta
                ponto.nome_popular_sugerido = identificacao.nome_popular
                ponto.nome_cientifico_sugerido = identificacao.nome_cientifico
                ponto.score_identificacao = identificacao.score * 100 if identificacao.score <= 1 else identificacao.score
                ponto.status_identificacao = identificacao.status_identificacao
                ponto.payload_resumido_validacao = {
                    **(ponto.payload_resumido_validacao or {}),
                    "resolucao_nome": {
                        "nome_popular_escolhido": nome_popular,
                        "nome_cientifico_resolvido": (planta.nome_cientifico or nome_cientifico or "").strip(),
                        "origem": (request.POST.get("nome_resolucao_origem") or "manual").strip(),
                    },
                }
                try:
                    with transaction.atomic():
                        _apply_manual_food_fields_to_ponto(ponto, payload=form.cleaned_data)
                        ponto.save()
                        _sync_manual_fields_to_planta(ponto)
                    messages.success(request, "Contribuição cadastrada! Aguarde a validação.")
                    registrar_acao_gamificada(request.user, 'cadastro')

                    # Enriquecimento taxonômico (não bloqueia o cadastro se falhar)
                    nome_para_enriquecer = identificacao.nome_cientifico or nome_cientifico
                    if nome_para_enriquecer:
                        try:
                            ponto.nome_cientifico_submetido = nome_para_enriquecer
                            ponto.save(update_fields=["nome_cientifico_submetido", "atualizado_em"])
                            plant_enrichment_pipeline.run_for_ponto(
                                ponto,
                                include_trefle=True,
                                origem="cadastro_web",
                            )
                        except Exception as exc:
                            logger.warning("Enriquecimento falhou no cadastro (ponto %s): %s", ponto.pk, exc)

                    return redirect('painel_contribuicoes')
                except IntegrityError:
                    logger.exception("Falha ao salvar PontoPANC por integridade.")
                    form.add_error(None, "Não foi possível salvar o ponto com os dados atuais. Revise os campos da planta e tente novamente.")
        messages.error(request, "Revise os campos destacados antes de enviar.")
    else:
        form = PontoPANCForm()
    plantas = PlantaReferencial.objects.order_by('nome_popular')
    return render(request, 'mapping/cadastrar_ponto.html', {
        'form': form,
        'plantas': plantas,
        'identificacao_preview': identificacao_preview,
    })


@login_required
def editar_ponto(request, pk):
    # Use colaborador para checar permissão de edição:
    ponto = get_object_or_404(PontoPANC, pk=pk)
    if ponto.colaborador != request.user.username and not request.user.is_superuser:
        messages.error(request, "Você não tem permissão para editar este ponto.")
        return redirect('painel_contribuicoes')

    if request.method == 'POST':
        form = PontoPANCForm(request.POST, request.FILES, instance=ponto)
        if form.is_valid():
            ponto = form.save(commit=False)
            ponto.cidade = request.POST.get('cidade', '').strip()
            ponto.estado = request.POST.get('estado', '').strip()
            ponto.bairro = request.POST.get('bairro', '').strip()
            ponto.endereco = request.POST.get('endereco', '').strip()
            ponto.numero = request.POST.get('numero', '').strip()
            nome_popular = (form.cleaned_data.get("nome_popular") or "").strip()
            nome_cientifico = (form.cleaned_data.get("nome_cientifico") or "").strip()
            foto = form.cleaned_data.get("foto") or ponto.foto

            identificacao = plant_identification_service.identify(
                foto=foto,
                nome_popular=nome_popular,
                nome_cientifico=nome_cientifico,
                lat=ponto.localizacao.y if ponto.localizacao else None,
                lon=ponto.localizacao.x if ponto.localizacao else None,
            )
            planta, detalhe_resolucao = plant_identification_service.resolve_or_create_planta(
                nome_popular=nome_popular,
                nome_cientifico=nome_cientifico,
                identification=identificacao,
            )
            if not planta:
                form.add_error("nome_popular", detalhe_resolucao)
            else:
                ponto.planta = planta
                ponto.nome_popular_sugerido = identificacao.nome_popular
                ponto.nome_cientifico_sugerido = identificacao.nome_cientifico
                ponto.score_identificacao = identificacao.score * 100 if identificacao.score <= 1 else identificacao.score
                ponto.status_identificacao = identificacao.status_identificacao
                ponto.payload_resumido_validacao = {
                    **(ponto.payload_resumido_validacao or {}),
                    "resolucao_nome": {
                        "nome_popular_escolhido": nome_popular,
                        "nome_cientifico_resolvido": (planta.nome_cientifico or nome_cientifico or "").strip(),
                        "origem": (request.POST.get("nome_resolucao_origem") or "manual").strip(),
                    },
                }
                try:
                    with transaction.atomic():
                        _apply_manual_food_fields_to_ponto(ponto, payload=form.cleaned_data)
                        ponto.save()
                        _sync_manual_fields_to_planta(ponto)
                    messages.success(request, "Contribuição atualizada!")

                    # Re-enriquecimento taxonômico na edição
                    nome_para_enriquecer = identificacao.nome_cientifico or nome_cientifico
                    if nome_para_enriquecer:
                        try:
                            ponto.nome_cientifico_submetido = nome_para_enriquecer
                            ponto.save(update_fields=["nome_cientifico_submetido", "atualizado_em"])
                            plant_enrichment_pipeline.run_for_ponto(
                                ponto,
                                include_trefle=True,
                                origem="edicao_web",
                            )
                        except Exception as exc:
                            logger.warning("Enriquecimento falhou na edição (ponto %s): %s", ponto.pk, exc)

                    return redirect('painel_contribuicoes')
                except IntegrityError:
                    logger.exception("Falha ao atualizar PontoPANC por integridade.")
                    form.add_error(None, "Não foi possível atualizar o ponto com os dados atuais.")
        messages.error(request, "Revise os campos destacados antes de salvar.")
    else:
        initial = {}
        if ponto.planta:
            initial = {
                'nome_popular': ponto.planta.nome_popular,
                'nome_cientifico': ponto.planta.nome_cientifico,
            }
        form = PontoPANCForm(instance=ponto, initial=initial)
    plantas = PlantaReferencial.objects.order_by('nome_popular')
    return render(request, 'mapping/cadastrar_ponto.html', {
        'form': form,
        'plantas': plantas,
        'edicao': True,
        'ponto': ponto,
    })


@login_required

def reverse_geocode(request):
    
    lat = request.GET.get("lat")
    lng = request.GET.get("lng")

    try:
        url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lng}&addressdetails=1"
        headers = {"User-Agent": "ColaboraPANC"}
        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status()
        return JsonResponse(response.json())
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)

@login_required
def remover_ponto(request, pk):
    ponto = get_object_or_404(PontoPANC, pk=pk)
    if ponto.colaborador != request.user.username and not request.user.is_superuser:
        messages.error(request, "Você não tem permissão para remover este ponto.")
        return redirect('painel_contribuicoes')
    ponto.delete()
    messages.success(request, "Ponto removido com sucesso!")
    return redirect("painel_contribuicoes")


# =======================
# AUTOCOMPLETE E API DE APOIO
# =======================

@login_required
def buscar_nome_cientifico(request):
    nome = request.GET.get('nome_popular', '').strip()
    resolved = _resolver_nome_cientifico_por_sugestao(nome)
    return JsonResponse(resolved)

@login_required
def autocomplete_nome_popular(request):
    termo = request.GET.get('term', '').strip().lower()
    detalhado = request.GET.get("detailed", "").lower() in {"1", "true", "sim", "yes"}
    sugestoes = _montar_sugestoes_nomes_populares(termo, limite=10)
    if detalhado:
        return JsonResponse(sugestoes, safe=False)
    return JsonResponse([item["nome_popular"] for item in sugestoes], safe=False)

# =======================
# API DE IDENTIFICAÇÃO AUTOMÁTICA
# =======================

@csrf_exempt
@login_required
def api_identificar(request):
    if request.method == "POST" and request.FILES.get("foto"):
        foto = request.FILES['foto']
        normalizado = mobile_parity_service.identificar_por_imagem(foto)
        resultados = normalizado.payload.get("candidatos") or []
        if not resultados and normalizado.payload.get("sucesso"):
            resultados = [{
                "nome_popular": normalizado.payload.get("nome_popular", ""),
                "nome_cientifico": normalizado.payload.get("nome_cientifico", ""),
                "score": normalizado.payload.get("score", 0.0),
                "fonte": normalizado.payload.get("metodo", "pipeline_unificada"),
            }]
        if not resultados:
            resultados = identificar_planta_api(foto)
        if not isinstance(resultados, list):
            resultados = [{'erro': 'Resposta inesperada da API de identificação.'}]
        return JsonResponse(resultados, safe=False)
    return JsonResponse([{'erro': 'Método não suportado ou foto ausente.'}], safe=False, status=400)

@login_required
def teste_identificacao(request):
    return render(request, 'mapping/teste_identificacao.html')

# =======================
# VALIDAÇÃO (ESPECIALISTA/REVISOR)
# =======================

@login_required
@user_passes_test(is_revisor)
def painel_validacao(request):
    pontos = (
        PontoPANC.objects.filter(status_validacao='pendente')
        .exclude(pareceres__especialista=request.user)
        .order_by('-criado_em')
    )
    return render(request, 'mapping/painel_validacao.html', {'pontos': pontos})

@login_required
@user_passes_test(is_revisor)
def validar_ponto(request, ponto_id):
    ponto = get_object_or_404(PontoPANC, id=ponto_id)
    if request.method == "POST":
        parecer = request.POST.get('parecer')
        comentario = request.POST.get('comentario', '')
        ParecerValidacao.objects.create(
            ponto=ponto,
            especialista=request.user,
            parecer=parecer,
            comentario=comentario
        )
        pareceres = ParecerValidacao.objects.filter(ponto=ponto)
        aprovados = pareceres.filter(parecer='aprovado').count()
        reprovados = pareceres.filter(parecer='reprovado').count()
        pendencias = pareceres.filter(parecer='pendencia').count()
        if aprovados >= 2:
            ponto.status_validacao = 'aprovado'
        elif reprovados >= 2:
            ponto.status_validacao = 'reprovado'
        elif pendencias >= 1:
            ponto.status_validacao = 'pendencia'
        ponto.save()
        messages.success(request, "Parecer registrado com sucesso!")
        registrar_acao_gamificada(request.user, 'revisao')

        return redirect('painel_validacao')
    return render(request, 'mapping/validar_ponto.html', {'ponto': ponto})

# =======================
# GRUPOS / COMUNIDADES
# =======================

@login_required
def painel_grupos(request):
    grupos = Grupo.objects.filter(membros=request.user)
    return render(request, 'mapping/painel_grupos.html', {'grupos': grupos})

# =======================
# GAMIFICAÇÃO / CONQUISTAS
# =======================

@login_required
def minhas_conquistas(request):
    badges_usuario = UsuarioBadge.objects.filter(usuario=request.user)
    return render(request, 'mapping/minhas_conquistas.html', {'badges': badges})

def conquistas_disponiveis(request):
    # Esqueleto para evitar erro caso view esteja só no urls.py
    return render(request, 'mapping/conquistas_disponiveis.html')

def ranking_usuarios(request):
    # Esqueleto para evitar erro caso view esteja só no urls.py
    return render(request, 'mapping/ranking_usuarios.html')

def historico_gamificacao(request):
    # Esqueleto para evitar erro caso view esteja só no urls.py
    return render(request, 'mapping/historico_gamificacao.html')

# =======================
# FEEDBACK
# =======================

@login_required
def enviar_feedback(request):
    if request.method == 'POST':
        mensagem = request.POST.get('mensagem', '').strip()
        ponto_id = request.POST.get('ponto_id')
        ponto = PontoPANC.objects.filter(id=ponto_id).first() if ponto_id else None
        Feedback.objects.create(usuario=request.user, mensagem=mensagem, ponto=ponto)
        # Pontuação feedback
        adicionar_pontos(request.user, 2, "Enviou Feedback")
        messages.success(request, "Feedback enviado com sucesso!")
        return redirect('obrigado')
    return render(request, 'mapping/enviar_feedback.html')



@login_required
def lista_feedbacks(request):
    feedbacks = Feedback.objects.all().order_by('-criado_em')
    return render(request, 'mapping/lista_feedbacks.html', {'feedbacks': feedbacks})

def obrigado(request):
    # View simples de agradecimento pós-feedback
    return render(request, 'mapping/obrigado.html')



# =======================
# LISTA DE COMUNIDADES / GRUPOS
# =======================

def lista_comunidades(request):
    grupos = Grupo.objects.all()
    return render(request, 'mapping/lista_comunidades.html', {'grupos': grupos})
    
@login_required
def meus_grupos(request):
    grupos = Grupo.objects.filter(membros=request.user)
    return render(request, 'mapping/meus_grupos.html', {'grupos': grupos})    
    

# =============================
# Painel Principal de Gamificação
# =============================
@login_required
def painel_gamificacao(request):
    usuario = request.user

    # Pontuação e nível do usuário (garante existência)
    pontuacao = PontuacaoUsuario.objects.get_or_create(usuario=usuario)[0]

    # Badges conquistados pelo usuário (mais recentes primeiro)
    badges_usuario = UsuarioBadge.objects.filter(usuario=usuario).select_related('badge').order_by('-data_conquista')

    # Missões ativas e separação entre pendentes/concluídas
    missoes_ativas = Missao.objects.filter(ativa=True)
    missoes_usuario = MissaoUsuario.objects.filter(usuario=usuario)
    concluidas = missoes_ativas.filter(
        id__in=missoes_usuario.filter(completada=True).values_list('missao_id', flat=True)
    )
    pendentes = missoes_ativas.exclude(
        id__in=missoes_usuario.filter(completada=True).values_list('missao_id', flat=True)
    )

    # Top 10 usuários por pontuação
    ranking_usuarios = PontuacaoUsuario.objects.select_related('usuario').order_by('-pontos')[:10]

    # Histórico de gamificação do usuário (últimas 20 ações)
    historico = HistoricoGamificacao.objects.filter(usuario=usuario).order_by('-data')[:20]

    # Botão flutuante de ação especial ou notificação (se houver)
    botao_flutuante = BotaoFlutuante.objects.filter(usuario=usuario, exibido=True).first()

    # Contexto para o template
    context = {
        "pontuacao": pontuacao,
        "badges_usuario": badges_usuario,
        "pendentes": pendentes,
        "concluidas": concluidas,
        "ranking_usuarios": ranking_usuarios,
        "historico": historico,
        "botao_flutuante": botao_flutuante,
    }
    return render(request, "mapping/painel_gamificacao.html", context)
# =============================
# Minhas Conquistas
# =============================
@login_required
def minhas_conquistas(request):
    # Recupera as conquistas (badges) do usuário usando a tabela intermediária UsuarioBadge
    conquistas = UsuarioBadge.objects.filter(usuario=request.user).select_related('badge').order_by('-data_conquista')
    pontuacao = PontuacaoUsuario.objects.get_or_create(usuario=request.user)[0]
    return render(request, "mapping/minhas_conquistas.html", {
        "conquistas": conquistas,
        "pontuacao": pontuacao
    })
# =============================
# Ranking Geral de Usuários
# =============================
@login_required
def ranking_usuarios(request):
    ranking = PontuacaoUsuario.objects.select_related('usuario').order_by('-pontos', '-nivel')[:100]
    ranking_revisores = RankingRevisor.objects.select_related('usuario').order_by('-pontuacao', '-avaliacoes')[:50]
    return render(request, "mapping/ranking_usuarios.html", {
        "ranking": ranking,
        "ranking_revisores": ranking_revisores,
    })

# =============================
# Conquistas Disponíveis
# =============================
@login_required
def conquistas_disponiveis(request):
    todas_badges = Badge.objects.values('nome', 'descricao', 'icone').distinct()
    return render(request, "mapping/conquistas_disponiveis.html", {"badges": todas_badges})

# =============================
# Histórico de Gamificação
# =============================
@login_required
def historico_gamificacao(request):
    historico = HistoricoGamificacao.objects.filter(usuario=request.user).order_by('-data')[:100]
    return render(request, "mapping/historico_gamificacao.html", {"historico": historico})

# =============================
# Missões: listar, calcular progresso, concluir e sugerir
# =============================
from django.utils import timezone

@login_required
def missoes(request):
    usuario = request.user
    hoje = timezone.now().date()
    semana_atual = hoje - timezone.timedelta(days=7)

    def get_progresso(missao, usuario):
        # Cálculo automático por tipo
        if missao.tipo == 'diaria':
            progresso = PontoPANC.objects.filter(colaborador=usuario.username, criado_em__date=hoje).count()
        elif missao.tipo == 'semanal':
            progresso = PontoPANC.objects.filter(colaborador=usuario.username, criado_em__date__gte=semana_atual).count()
        elif missao.tipo == 'meta':
            progresso = PontoPANC.objects.filter(colaborador=usuario.username).count()
        elif missao.tipo == 'especial' and 'feedback' in missao.titulo.lower():
            progresso = Feedback.objects.filter(usuario=usuario).count()
        else:
            progresso = 0
        meta = missao.meta or 1
        return progresso, meta

    missoes_ativas = Missao.objects.filter(ativa=True)
    missoes_diarias, missoes_semanais, missoes_especiais = [], [], []

    for m in missoes_ativas:
        progresso, meta = get_progresso(m, usuario)
        completa = progresso >= meta

        # Atualiza ou cria progresso da missão para o usuário
        mu, _ = MissaoUsuario.objects.get_or_create(usuario=usuario, missao=m)
        mu.progresso = progresso
        mu.completa = completa
        if completa and not mu.data_conclusao:
            mu.data_conclusao = timezone.now()
        mu.save()

        missao_dict = {
            'id': m.id,
            'titulo': m.titulo,
            'descricao': m.descricao,
            'tipo': m.tipo,
            'pontos': m.pontos,
            'meta': meta,
            'progresso': progresso,
            'progresso_percent': min(100, int(100 * progresso / meta)) if meta else 100,
            'completa': completa,
            'secreta': m.secreta,
        }
        if m.tipo == 'diaria':
            missoes_diarias.append(missao_dict)
        elif m.tipo == 'semanal':
            missoes_semanais.append(missao_dict)
        else:
            missoes_especiais.append(missao_dict)

    ctx = {
        'missoes_diarias': missoes_diarias,
        'missoes_semanais': missoes_semanais,
        'missoes_especiais': missoes_especiais,
    }
    return render(request, "mapping/missoes.html", ctx)


@login_required
def concluir_missao(request, missao_id):
    missao = get_object_or_404(Missao, id=missao_id, ativa=True)
    mu, created = MissaoUsuario.objects.get_or_create(usuario=request.user, missao=missao)
    if not mu.completa:
        mu.completa = True
        mu.data_conclusao = timezone.now()
        mu.save()
        # Pontuação
        pontuacao = PontuacaoUsuario.objects.get_or_create(usuario=request.user)[0]
        pontuacao.pontos += missao.pontos
        pontuacao.atualizar_nivel()
        HistoricoGamificacao.objects.create(
            usuario=request.user,
            acao=f"Missão concluída: {missao.titulo}",
            pontos=missao.pontos,
            referencia=f"Missao:{missao.id}"
        )
        messages.success(request, "Missão concluída! Pontos adicionados.")
    return redirect("missoes")


@login_required
def sugerir_missao(request):
    if request.method == "POST":
        form = SugestaoMissaoForm(request.POST)
        if form.is_valid():
            sugestao = form.save(commit=False)
            sugestao.usuario = request.user
            sugestao.save()
            messages.success(request, "Sugestão de missão enviada para análise!")
            return redirect("missoes")
    else:
        form = SugestaoMissaoForm()
    return render(request, "mapping/sugerir_missao.html", {"form": form})


# =============================
# Botão flutuante: apagar ao subir de nível
# =============================
@login_required
def apagar_botao_flutuante(request):
    BotaoFlutuante.objects.filter(usuario=request.user).delete()
    return JsonResponse({"ok": True})

@login_required
def remover_botao_flutuante(request):
    if request.method == "POST":
        BotaoFlutuante.objects.filter(usuario=request.user).delete()
        return JsonResponse({"status": "removido"})
    return JsonResponse({"erro": "Requisição inválida"}, status=400)
    
# =============================
# Painel de Administração de Gamificação
# =============================

@login_required
def painel_admin_gamificacao(request):
    # KPIs
    total_usuarios = User.objects.count()
    total_pontos = PontuacaoUsuario.objects.aggregate(Sum('pontos'))['pontos__sum'] or 0
    total_missoes_concluidas = HistoricoGamificacao.objects.filter(acao__icontains="Missão concluída").count()
    total_badges = Badge.objects.count()
    total_sugestoes = SugestaoMissao.objects.count()
    kpis = [
        {"titulo": "Usuários ativos", "valor": total_usuarios, "icone": "bi bi-person-fill", "cor": "info"},
        {"titulo": "Pontos distribuídos", "valor": total_pontos, "icone": "bi bi-coin", "cor": "warning"},
        {"titulo": "Missões concluídas", "valor": total_missoes_concluidas, "cor": "success", "icone": "bi bi-stars"},
        {"titulo": "Conquistas atribuídas", "valor": total_badges, "icone": "bi bi-trophy", "cor": "primary"},
        {"titulo": "Sugestões recebidas", "valor": total_sugestoes, "icone": "bi bi-chat-dots", "cor": "secondary"},
    ]

    # Gráficos e Mapa
    cadastros_labels, cadastros_data = get_cadastros_mensais()
    top_usuarios_labels, top_usuarios_data = get_top_usuarios()
    pontos_geojson = json.dumps(pontos_to_geojson())

    # Últimos registros
    historico = HistoricoGamificacao.objects.select_related('usuario').order_by('-data')[:20]
    missoes_recent = Missao.objects.order_by('-data_criacao')[:6]
    conquistas_recent = Badge.objects.order_by('-data_criacao')[:6]  # <<=== Corrigido aqui!
    feedbacks_recent = Feedback.objects.order_by('-criado_em')[:6]

    # Rankings
    ranking_usuarios = PontuacaoUsuario.objects.select_related('usuario').order_by('-pontos')[:10]
    ranking_revisores = RankingRevisor.objects.order_by('-pontuacao')[:10]

    # Sugestões
    sugestoes = SugestaoMissao.objects.all().order_by('-criado_em')[:10]

    return render(request, "mapping/painel_admin_gamificacao.html", {
        "kpis": kpis,
        "historico": historico,
        "missoes_recent": missoes_recent,
        "conquistas_recent": conquistas_recent,
        "feedbacks_recent": feedbacks_recent,
        "cadastros_labels": json.dumps(cadastros_labels),
        "cadastros_data": json.dumps(cadastros_data),
        "top_usuarios_labels": json.dumps(top_usuarios_labels),
        "top_usuarios_data": json.dumps(top_usuarios_data),
        "pontos_geojson": pontos_geojson,
        "ranking_usuarios": ranking_usuarios,
        "ranking_revisores": ranking_revisores,
        "sugestoes": sugestoes,
        "total_badges": total_badges,
        "total_missoes": Missao.objects.filter(ativa=True).count(),
        "total_usuarios": total_usuarios,
        "total_sugestoes": total_sugestoes,
    })

# =============================
# Funções auxiliares para outras lógicas
# =============================
# ...exemplo de uso:
def atualizar_pontuacao_ao_realizar_acao(usuario, pontos, acao, referencia=''):
    pontuacao = PontuacaoUsuario.objects.get_or_create(usuario=usuario)[0]
    pontuacao.pontos += pontos
    pontuacao.atualizar_nivel()
    HistoricoGamificacao.objects.create(
        usuario=usuario,
        acao=acao,
        pontos=pontos,
        referencia=referencia
    )
 
# =============================
# Ranking Revisor
# =============================

@login_required
@user_passes_test(lambda u: u.is_superuser or u.groups.filter(name='Revisores').exists())
def ranking_revisores(request):
    ranking = RankingRevisor.objects.order_by('-pontuacao')[:50]  # Ajuste o campo de pontuação conforme seu model
    return render(request, 'mapping/ranking_revisores.html', {'ranking': ranking})
    
    
    
@user_passes_test(lambda u: u.is_superuser)
def criar_missao(request):
    # Sua lógica para criar missão (formulário, etc)
    return render(request, "mapping/criar_missao.html")    

# =============================
# Conquista Criar
# =============================

@login_required
@user_passes_test(lambda u: u.is_superuser)
def criar_conquista(request):
    if request.method == "POST":
        nome = request.POST.get('nome', '').strip()
        descricao = request.POST.get('descricao', '').strip()
        username = request.POST.get('usuario', '').strip()

        usuario = None
        if username:
            from django.contrib.auth.models import User
            usuario = User.objects.filter(username=username).first()

        if nome and descricao:
            Badge.objects.create(
                nome=nome,
                descricao=descricao,
                usuario=usuario
            )
            messages.success(request, "Conquista criada/atribuída com sucesso!")
            return redirect('painel_admin_gamificacao')  # ajuste para sua URL principal do painel
        else:
            messages.error(request, "Preencha todos os campos obrigatórios.")

    return redirect('painel_admin_gamificacao')
    
@login_required
def painel_admin_gamificacao(request):
    # Indicadores (exemplo)
    total_usuarios = User.objects.count()
    total_pontos = PontuacaoUsuario.objects.aggregate(Sum('pontos'))['pontos__sum'] or 0
    total_missoes_concluidas = HistoricoGamificacao.objects.filter(acao__icontains="Missão concluída").count()
    total_badges = Badge.objects.count()
    # total_grupos = ... # coloque sua consulta de grupos aqui

    kpis = [
        {"titulo": "Usuários ativos", "valor": total_usuarios, "icone": "bi bi-person-fill", "cor": "info"},
        {"titulo": "Pontos distribuídos", "valor": total_pontos, "icone": "bi bi-coin", "cor": "warning"},
        {"titulo": "Missões concluídas", "valor": total_missoes_concluidas, "cor": "success", "icone": "bi bi-stars"},
        {"titulo": "Conquistas atribuídas", "valor": total_badges, "icone": "bi bi-trophy", "cor": "primary"},
    ]

    # Dados para gráficos (preencha conforme sua função utilitária)
    cadastros_labels, cadastros_data = get_cadastros_mensais()
    top_usuarios_labels, top_usuarios_data = get_top_usuarios()
    pontos_geojson = pontos_to_geojson()

    # Últimas ações/itens
    historico = HistoricoGamificacao.objects.select_related('usuario').order_by('-data')[:20]
    missoes_recent = Missao.objects.order_by('-data_criacao')[:6]
    conquistas_recent = Badge.objects.order_by('-data_criacao')[:6]
    feedbacks_recent = Feedback.objects.order_by('-criado_em')[:6]

    return render(request, "mapping/painel_admin_gamificacao.html", {
        "kpis": kpis,
        "historico": historico,
        "missoes_recent": missoes_recent,
        "conquistas_recent": conquistas_recent,
        "feedbacks_recent": feedbacks_recent,
        "cadastros_labels": cadastros_labels,
        "cadastros_data": cadastros_data,
        "top_usuarios_labels": top_usuarios_labels,
        "top_usuarios_data": top_usuarios_data,
        "pontos_geojson": pontos_geojson,
    })


# =============================
# CRUD Missões
# =============================

@user_passes_test(lambda u: u.is_superuser)
def criar_missao(request):
    if request.method == "POST":
        titulo = request.POST.get('titulo', '').strip()
        descricao = request.POST.get('descricao', '').strip()
        tipo = request.POST.get('tipo', 'especial')
        pontos = int(request.POST.get('pontos', 1))
        ativa = bool(request.POST.get('ativa', False))
        if titulo and descricao:
            Missao.objects.create(
                titulo=titulo,
                descricao=descricao,
                tipo=tipo,
                pontos=pontos,
                ativa=ativa,
            )
            messages.success(request, "Missão criada com sucesso!")
        else:
            messages.error(request, "Preencha todos os campos obrigatórios.")
    return redirect('painel_admin_gamificacao')

@user_passes_test(lambda u: u.is_superuser)
def editar_missao(request, missao_id):
    missao = get_object_or_404(Missao, id=missao_id)
    if request.method == "POST":
        missao.titulo = request.POST.get('titulo', missao.titulo)
        missao.descricao = request.POST.get('descricao', missao.descricao)
        missao.tipo = request.POST.get('tipo', missao.tipo)
        missao.pontos = int(request.POST.get('pontos', missao.pontos))
        missao.ativa = bool(request.POST.get('ativa', missao.ativa))
        missao.save()
        messages.success(request, "Missão atualizada com sucesso!")
        return redirect('painel_admin_gamificacao')
    return render(request, "mapping/editar_missao.html", {"missao": missao})

@user_passes_test(lambda u: u.is_superuser)
def excluir_missao(request, missao_id):
    missao = get_object_or_404(Missao, id=missao_id)
    missao.delete()
    messages.success(request, "Missão excluída com sucesso!")
    return redirect('painel_admin_gamificacao')

@user_passes_test(lambda u: u.is_superuser)
def desativar_missao(request, missao_id):
    missao = get_object_or_404(Missao, id=missao_id)
    missao.ativa = not missao.ativa
    missao.save()
    status = "ativada" if missao.ativa else "desativada"
    messages.success(request, f"Missão {status} com sucesso!")
    return redirect('painel_admin_gamificacao')

# =============================
# CRUD Conquistas (Badges)
# =============================

@user_passes_test(lambda u: u.is_superuser)
def criar_conquista(request):
    if request.method == "POST":
        nome = request.POST.get('nome', '').strip()
        descricao = request.POST.get('descricao', '').strip()
        username = request.POST.get('usuario', '').strip()
        icone = request.FILES.get('icone')
        usuario = User.objects.filter(username=username).first() if username else None
        if nome and descricao:
            Badge.objects.create(
                nome=nome,
                descricao=descricao,
                usuario=usuario,
                icone=icone,
            )
            messages.success(request, "Conquista criada/atribuída com sucesso!")
        else:
            messages.error(request, "Preencha todos os campos obrigatórios.")
    return redirect('painel_admin_gamificacao')

@user_passes_test(lambda u: u.is_superuser)
def editar_conquista(request, badge_id):
    badge = get_object_or_404(Badge, id=badge_id)
    if request.method == "POST":
        badge.nome = request.POST.get('nome', badge.nome)
        badge.descricao = request.POST.get('descricao', badge.descricao)
        username = request.POST.get('usuario', badge.usuario.username if badge.usuario else '')
        badge.usuario = User.objects.filter(username=username).first() if username else None
        if request.FILES.get('icone'):
            badge.icone = request.FILES.get('icone')
        badge.save()
        messages.success(request, "Conquista atualizada com sucesso!")
        return redirect('painel_admin_gamificacao')
    return render(request, "mapping/editar_conquista.html", {"badge": badge})

@user_passes_test(lambda u: u.is_superuser)
def excluir_conquista(request, badge_id):
    badge = get_object_or_404(Badge, id=badge_id)
    badge.delete()
    messages.success(request, "Conquista excluída com sucesso!")
    return redirect('painel_admin_gamificacao')

# =============================
# Feedbacks - Admin View
# =============================

@user_passes_test(lambda u: u.is_superuser)
def admin_lista_feedbacks(request):
    feedbacks = Feedback.objects.all().order_by('-criado_em')
    return render(request, 'mapping/admin_lista_feedbacks.html', {'feedbacks': feedbacks})



# =============================
# Exportação de Relatórios
# =============================

@user_passes_test(lambda u: u.is_superuser)
def exportar_relatorio(request):
    # Exemplo: exportar pontos para CSV
    import csv
    from django.http import HttpResponse

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="pontos_panc.csv"'
    writer = csv.writer(response)
    writer.writerow(['ID', 'Nome Popular', 'Nome Científico', 'Cidade', 'Estado', 'Data'])

    for p in PontoPANC.objects.all():
        writer.writerow([p.id, p.planta.nome_popular if p.planta else '', p.planta.nome_cientifico if p.planta else '', p.cidade, p.estado, p.criado_em])

    return response



# =============================
# GAMIFICAÇÃO COLABORATIVA USUÁRIO (MELHORADA)
# =============================


@login_required
def criar_missao_usuario(request):
    if request.method == 'POST':
        titulo = request.POST.get('titulo', '').strip()
        descricao = request.POST.get('descricao', '').strip()
        pontos = int(request.POST.get('pontos', 1))
        pontos = min(pontos, 100)
        tipo = request.POST.get('tipo', 'especial')
        if pontos_disponiveis_para_criador(request.user) >= pontos:
            missao = Missao.objects.create(
                titulo=titulo,
                descricao=descricao,
                tipo=tipo,
                pontos=pontos,
                ativa=True,
                criador=request.user
            )
            adicionar_pontos(request.user, pontos, "Criou Desafio", f"Missao:{missao.id}")
            messages.success(request, "Missão criada!")
            return redirect('minhas_missoes')
        else:
            messages.error(request, "Limite diário de pontos para criação de desafios atingido (100 pontos).")
    return render(request, 'mapping/criar_missao_usuario.html')


@login_required
def minhas_missoes(request):
    """
    Mostra as missões criadas pelo usuário logado.
    """
    minhas = Missao.objects.filter(criador=request.user).order_by('-data_criacao')
    return render(request, "mapping/minhas_missoes.html", {"minhas": minhas})


@login_required
def missoes_colaborativas(request):
    """
    Lista todas as missões colaborativas (ativas) e status do usuário.
    """
    missoes_ativas = Missao.objects.filter(ativa=True)
    # Todos os objetos MissaoUsuario do usuário (participação e conclusão)
    minhas_missao_usuario = MissaoUsuario.objects.filter(usuario=request.user)
    minhas_concluidas_map = {mu.missao_id: mu for mu in minhas_missao_usuario if mu.completada}
    minhas_participacoes_ids = [mu.missao_id for mu in minhas_missao_usuario]
    # Separar pendentes das concluídas (pelo usuário)
    pendentes = missoes_ativas.exclude(id__in=minhas_concluidas_map.keys())
    concluidas_info = []
    for mu in minhas_concluidas_map.values():
        concluidas_info.append({
            "missao": mu.missao,
            "data_conclusao": mu.data_conclusao,
            "pontos": mu.missao.pontos,
            "criador": mu.missao.criador,
        })
    return render(request, "mapping/missoes_colaborativas.html", {
        "pendentes": pendentes,
        "concluidas_info": concluidas_info,
        "minhas_participacoes_ids": minhas_participacoes_ids,  # útil para "botão Participar" desabilitar
    })


@login_required
def participar_missao(request, missao_id):
    """
    Usuário entra em uma missão colaborativa para participar.
    """
    missao = get_object_or_404(Missao, id=missao_id, ativa=True)
    mu, created = MissaoUsuario.objects.get_or_create(usuario=request.user, missao=missao)
    if created:
        messages.success(request, f"Você agora participa da missão '{missao.titulo}'!")
    else:
        messages.info(request, "Você já está participando desta missão.")
    return redirect('missoes_colaborativas')



@login_required
def concluir_missao_usuario(request, missao_id):
    missao = get_object_or_404(Missao, id=missao_id, ativa=True)
    mu, created = MissaoUsuario.objects.get_or_create(usuario=request.user, missao=missao)
    if not mu.completada:
        mu.completada = True
        mu.data_conclusao = timezone.now()
        mu.save()
        # Pontuação automática (usar valor definido na missão)
        adicionar_pontos(request.user, missao.pontos, f"Concluiu Missão: {missao.titulo}", f"Missao:{missao.id}")
        messages.success(request, "Missão concluída! Pontos adicionados.")
    return redirect("missoes_colaborativas")

@login_required
def ranking_missao(request, missao_id):
    """
    Mostra o ranking de usuários que completaram determinada missão colaborativa.
    """
    missao = get_object_or_404(Missao, id=missao_id)
    ranking = (
        MissaoUsuario.objects.filter(missao=missao, completada=True)
        .select_related('usuario')
        .order_by('data_conclusao')  # Os primeiros a concluir aparecem no topo
    )
    return render(request, "mapping/ranking_missao.html", {
        "missao": missao,
        "ranking": ranking
    })


# =============================
# Gráficos do painel
# =============================

def get_cadastros_mensais():
    # Últimos 6 meses
    hoje = datetime.now()
    labels = []
    data = []
    for i in range(5, -1, -1):
        mes = hoje - timedelta(days=30*i)
        nome_mes = calendar.month_abbr[mes.month]
        labels.append(f'{nome_mes}/{mes.year}')
        data.append(
            User.objects.filter(date_joined__year=mes.year, date_joined__month=mes.month).count()
        )
    return labels, data

def get_top_usuarios():
    top_usuarios = PontuacaoUsuario.objects.select_related('usuario').order_by('-pontos')[:10]
    labels = [u.usuario.username for u in top_usuarios]
    data = [u.pontos for u in top_usuarios]
    return labels, data

def pontos_to_geojson():
    # Retorna os pontos como GeoJSON para o mapa (pode usar serializers, exemplo simplificado abaixo)
    pontos = PontoPANC.objects.all()
    features = []
    for p in pontos:
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [p.localizacao.x, p.localizacao.y]
            },
            "properties": {
                "nome": p.nome_popular,
                "cidade": p.cidade,
            }
        })
    return {
        "type": "FeatureCollection",
        "features": features,
    }
# =============================
# Exportação de CSV
# =============================

@login_required
def exportar_usuarios_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="usuarios.csv"'
    writer = csv.writer(response)
    writer.writerow(['ID', 'Usuário', 'E-mail', 'Data de cadastro', 'Pontos'])
    for u in User.objects.all():
        pontuacao = getattr(u, 'pontuacao', None)
        pontos = pontuacao.pontos if pontuacao else 0
        writer.writerow([u.id, u.username, u.email, u.date_joined, pontos])
    return response

@login_required
def exportar_pontos_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="pontos_panc.csv"'
    writer = csv.writer(response)
    writer.writerow(['ID', 'Nome popular', 'Cidade', 'Estado', 'Latitude', 'Longitude', 'Criado por'])
    for p in PontoPANC.objects.all():
        writer.writerow([
            p.id, p.nome_popular, p.cidade, p.estado, p.localizacao.y, p.localizacao.x,
            p.criado_por.username if p.criado_por else '-'
        ])
    return response

# =============================
# Alerta climatico
# =============================

from django.shortcuts import render
from .models import AlertaClimatico
from .serializers import PontoPANCSerializer

def historico_alertas(request):
    estado = request.GET.get("estado", "")
    ponto = request.GET.get("ponto", "")
    tipo = request.GET.get("tipo", "")
    
    alertas = AlertaClimatico.objects.select_related("ponto").all()

    # Filtro por estado (texto, parcial)
    if estado:
        alertas = alertas.filter(ponto__estado__icontains=estado)
    
    # Filtro por tipo de alerta (texto, parcial)
    if tipo:
        alertas = alertas.filter(tipo__icontains=tipo)

    # Filtro por ponto (ID OU nome)
    if ponto:
        if ponto.isdigit():  # Se é ID numérico
            alertas = alertas.filter(ponto__id=int(ponto))
        else:  # Nome parcial (case-insensitive)
            alertas = alertas.filter(ponto__nome_popular__icontains=ponto)
    
    alertas = alertas.order_by("-inicio")
    
    context = {
        "alertas": alertas,
        "estado": estado,
        "ponto": ponto,
        "tipo": tipo,
        "bootstrap_loaded": True  # ajuste conforme seu projeto
    }
    return render(request, "mapping/historico_alertas.html", context)
    
    # ========================================
# IMPORTS
# ========================================
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User, Group
from django.db.models import Count, Sum
import csv
import json
import requests
import calendar
from datetime import datetime, timedelta

from .models import (
    Missao, Badge, MissaoUsuario, HistoricoGamificacao, PontuacaoUsuario, SugestaoMissao,
    BotaoFlutuante, RankingRevisor,
    PontoPANC, PlantaReferencial, ParecerValidacao,
    Grupo, Feedback, UsuarioBadge
)
from .forms import PontoPANCForm, SugestaoMissaoForm
from .identificacao_api import identificar_planta_api
from .utils import adicionar_pontos, pontos_disponiveis_para_criador, registrar_acao_gamificada

# =======================
# DECORATORS DE PERMISSÃO
# =======================

def admin_required(view_func):
    return user_passes_test(lambda u: u.is_superuser)(view_func)

def revisor_required(view_func):
    return user_passes_test(lambda u: u.is_authenticated and (u.is_superuser or u.groups.filter(name="Revisores").exists()))(view_func)

# =======================
# UTILITÁRIOS GERAIS
# =======================

def buscar_cientifico(nome_popular):
    """Busca nome científico a partir do nome popular."""
    planta = PlantaReferencial.objects.filter(nome_popular__iexact=nome_popular.strip()).first()
    return planta.nome_cientifico if planta else ''

def is_revisor(user):
    """Checa se o usuário é do grupo de Revisores ou admin."""
    return user.is_authenticated and (user.is_superuser or user.groups.filter(name='Revisores').exists())

# =======================
# VIEWS PÚBLICAS — MAPA, DETALHE E API DE PONTOS
# =======================

def mapa(request):
    """
    Exibe o mapa público (acessível a visitantes, usuários logados, revisores e admin).
    Adiciona variáveis de contexto para filtros e exibição especial para revisores.
    """
    pontos = PontoPANC.objects.select_related('planta', 'grupo').all()
    cidades = PontoPANC.objects.values_list('cidade', flat=True).distinct()
    estados = PontoPANC.objects.values_list('estado', flat=True).distinct()
    grupos = Grupo.objects.all()
    # Flag para exibir funções extras no mapa para revisor/admin
    is_revisor_flag = False
    if request.user.is_authenticated:
        is_revisor_flag = (
            request.user.is_superuser or 
            request.user.groups.filter(name='Revisores').exists()
        )
    return render(request, 'mapping/mapa.html', {
        'pontos': pontos,
        'cidades': cidades,
        'estados': estados,
        'grupos': grupos,
        'is_revisor': is_revisor_flag,
    })

def detalhe_ponto(request, pk):
    """
    Página de detalhes do ponto individual (acessível a qualquer usuário, inclusive visitante).
    """
    ponto = get_object_or_404(PontoPANC, pk=pk)
    can_edit_ponto = request.user.is_authenticated and (
        request.user.is_superuser or ponto.criado_por_id == request.user.id or ponto.colaborador == request.user.username
    )
    eventos_ambientais = ponto.eventos_monitorados.order_by("-ocorrido_em")[:20]
    enriquecimento = None
    historico_enriquecimento = []
    if ponto.planta:
        planta = ponto.planta
        if planta.status_enriquecimento and planta.status_enriquecimento != 'pendente':
            enriquecimento = planta
        historico_enriquecimento = list(
            planta.historico_enriquecimento.order_by('-data')[:5].values('data', 'status', 'fontes_consultadas')
        )
    return render(request, 'mapping/detalhe_ponto.html', {
        'ponto': ponto,
        'can_edit_ponto': can_edit_ponto,
        'enriquecimento': enriquecimento,
        'historico_enriquecimento': historico_enriquecimento,
        'eventos_ambientais': eventos_ambientais,
    })

def api_pontos(request):
    """
    API pública (GET) para listar e filtrar pontos cadastrados no mapa.
    Permite filtros via querystring e retorna apenas pontos válidos (com localização).
    Indica no JSON se o usuário autenticado pode editar cada ponto.
    """
    try:
        pontos = (
            PontoPANC.objects
            .select_related("planta", "grupo")
            .prefetch_related(
                Prefetch(
                    "alertas",
                    queryset=AlertaClimatico.objects.order_by("-inicio"),
                    to_attr="alertas_ordenados",
                )
            )
            .all()
        )
        pontos = aplicar_filtros_pontos(request, pontos)

        foto = request.GET.get("foto", "").strip().lower()
        if foto in ("1", "sim", "true"):
            pontos = pontos.exclude(foto__isnull=True).exclude(foto="")
        elif foto in ("0", "nao", "false"):
            pontos = pontos.filter(Q(foto__isnull=True) | Q(foto=""))

        resultado = []
        for ponto in pontos:
            serializado = serializar_ponto_api(ponto)
            if serializado:
                serializado["pode_editar"] = (
                    request.user.is_authenticated and
                    (request.user.is_superuser or ponto.colaborador == request.user.username)
                )
                resultado.append(serializado)

        return JsonResponse(resultado, safe=False)
    except Exception:
        logger.exception("Erro em /api/pontos")
        return JsonResponse({"erro": "Erro interno."}, status=500)

# =======================
# CADASTRO / EDIÇÃO / REMOÇÃO
# =======================

@login_required
def painel_contribuicoes(request):
    pontos = PontoPANC.objects.filter(colaborador=request.user.username)
    return render(request, 'mapping/painel_contribuicoes.html', {'pontos': pontos})


@login_required
def cadastrar_ponto(request):
    identificacao_preview = None
    if request.method == 'POST':
        form = PontoPANCForm(request.POST, request.FILES)
        if form.is_valid():
            ponto = form.save(commit=False)
            ponto.colaborador = request.user.username
            ponto.cidade = request.POST.get('cidade', '').strip()
            ponto.estado = request.POST.get('estado', '').strip()
            ponto.bairro = request.POST.get('bairro', '').strip()
            ponto.endereco = request.POST.get('endereco', '').strip()
            ponto.numero = request.POST.get('numero', '').strip()
            ponto.status_validacao = 'pendente'

            nome_popular = (form.cleaned_data.get("nome_popular") or "").strip()
            nome_cientifico = (form.cleaned_data.get("nome_cientifico") or "").strip()
            foto = form.cleaned_data.get("foto")
            lat = ponto.localizacao.y if ponto.localizacao else None
            lon = ponto.localizacao.x if ponto.localizacao else None

            identificacao = plant_identification_service.identify(
                foto=foto,
                nome_popular=nome_popular,
                nome_cientifico=nome_cientifico,
                lat=lat,
                lon=lon,
            )
            identificacao_preview = {
                "nome_popular": identificacao.nome_popular,
                "nome_cientifico": identificacao.nome_cientifico,
                "score": identificacao.score,
                "fonte": identificacao.fonte,
            }
            planta, detalhe_resolucao = plant_identification_service.resolve_or_create_planta(
                nome_popular=nome_popular,
                nome_cientifico=nome_cientifico,
                identification=identificacao,
            )
            if not planta:
                form.add_error("nome_popular", detalhe_resolucao)
            else:
                ponto.planta = planta
                ponto.nome_popular_sugerido = identificacao.nome_popular
                ponto.nome_cientifico_sugerido = identificacao.nome_cientifico
                ponto.score_identificacao = identificacao.score * 100 if identificacao.score <= 1 else identificacao.score
                ponto.status_identificacao = identificacao.status_identificacao
                ponto.payload_resumido_validacao = {
                    **(ponto.payload_resumido_validacao or {}),
                    "resolucao_nome": {
                        "nome_popular_escolhido": nome_popular,
                        "nome_cientifico_resolvido": (planta.nome_cientifico or nome_cientifico or "").strip(),
                        "origem": (request.POST.get("nome_resolucao_origem") or "manual").strip(),
                    },
                }
                try:
                    with transaction.atomic():
                        _apply_manual_food_fields_to_ponto(ponto, payload=form.cleaned_data)
                        ponto.save()
                        _sync_manual_fields_to_planta(ponto)
                    messages.success(request, "Contribuição cadastrada! Aguarde a validação.")
                    registrar_acao_gamificada(request.user, 'cadastro')

                    # Enriquecimento taxonômico (não bloqueia o cadastro se falhar)
                    nome_para_enriquecer = identificacao.nome_cientifico or nome_cientifico
                    if nome_para_enriquecer:
                        try:
                            ponto.nome_cientifico_submetido = nome_para_enriquecer
                            ponto.save(update_fields=["nome_cientifico_submetido", "atualizado_em"])
                            plant_enrichment_pipeline.run_for_ponto(
                                ponto,
                                include_trefle=True,
                                origem="cadastro_web",
                            )
                        except Exception as exc:
                            logger.warning("Enriquecimento falhou no cadastro (ponto %s): %s", ponto.pk, exc)

                    return redirect('painel_contribuicoes')
                except IntegrityError:
                    logger.exception("Falha ao salvar PontoPANC por integridade.")
                    form.add_error(None, "Não foi possível salvar o ponto com os dados atuais. Revise os campos da planta e tente novamente.")
        messages.error(request, "Revise os campos destacados antes de enviar.")
    else:
        form = PontoPANCForm()
    plantas = PlantaReferencial.objects.order_by('nome_popular')
    return render(request, 'mapping/cadastrar_ponto.html', {
        'form': form,
        'plantas': plantas,
        'identificacao_preview': identificacao_preview,
    })


@login_required
def editar_ponto(request, pk):
    # Use colaborador para checar permissão de edição:
    ponto = get_object_or_404(PontoPANC, pk=pk)
    if ponto.colaborador != request.user.username and not request.user.is_superuser:
        messages.error(request, "Você não tem permissão para editar este ponto.")
        return redirect('painel_contribuicoes')

    if request.method == 'POST':
        form = PontoPANCForm(request.POST, request.FILES, instance=ponto)
        if form.is_valid():
            ponto = form.save(commit=False)
            ponto.cidade = request.POST.get('cidade', '').strip()
            ponto.estado = request.POST.get('estado', '').strip()
            ponto.bairro = request.POST.get('bairro', '').strip()
            ponto.endereco = request.POST.get('endereco', '').strip()
            ponto.numero = request.POST.get('numero', '').strip()
            nome_popular = (form.cleaned_data.get("nome_popular") or "").strip()
            nome_cientifico = (form.cleaned_data.get("nome_cientifico") or "").strip()
            foto = form.cleaned_data.get("foto") or ponto.foto

            identificacao = plant_identification_service.identify(
                foto=foto,
                nome_popular=nome_popular,
                nome_cientifico=nome_cientifico,
                lat=ponto.localizacao.y if ponto.localizacao else None,
                lon=ponto.localizacao.x if ponto.localizacao else None,
            )
            planta, detalhe_resolucao = plant_identification_service.resolve_or_create_planta(
                nome_popular=nome_popular,
                nome_cientifico=nome_cientifico,
                identification=identificacao,
            )
            if not planta:
                form.add_error("nome_popular", detalhe_resolucao)
            else:
                ponto.planta = planta
                ponto.nome_popular_sugerido = identificacao.nome_popular
                ponto.nome_cientifico_sugerido = identificacao.nome_cientifico
                ponto.score_identificacao = identificacao.score * 100 if identificacao.score <= 1 else identificacao.score
                ponto.status_identificacao = identificacao.status_identificacao
                ponto.payload_resumido_validacao = {
                    **(ponto.payload_resumido_validacao or {}),
                    "resolucao_nome": {
                        "nome_popular_escolhido": nome_popular,
                        "nome_cientifico_resolvido": (planta.nome_cientifico or nome_cientifico or "").strip(),
                        "origem": (request.POST.get("nome_resolucao_origem") or "manual").strip(),
                    },
                }
                try:
                    with transaction.atomic():
                        _apply_manual_food_fields_to_ponto(ponto, payload=form.cleaned_data)
                        ponto.save()
                        _sync_manual_fields_to_planta(ponto)
                    messages.success(request, "Contribuição atualizada!")

                    # Re-enriquecimento taxonômico na edição
                    nome_para_enriquecer = identificacao.nome_cientifico or nome_cientifico
                    if nome_para_enriquecer:
                        try:
                            ponto.nome_cientifico_submetido = nome_para_enriquecer
                            ponto.save(update_fields=["nome_cientifico_submetido", "atualizado_em"])
                            plant_enrichment_pipeline.run_for_ponto(
                                ponto,
                                include_trefle=True,
                                origem="edicao_web",
                            )
                        except Exception as exc:
                            logger.warning("Enriquecimento falhou na edição (ponto %s): %s", ponto.pk, exc)

                    return redirect('painel_contribuicoes')
                except IntegrityError:
                    logger.exception("Falha ao atualizar PontoPANC por integridade.")
                    form.add_error(None, "Não foi possível atualizar o ponto com os dados atuais.")
        messages.error(request, "Revise os campos destacados antes de salvar.")
    else:
        initial = {}
        if ponto.planta:
            initial = {
                'nome_popular': ponto.planta.nome_popular,
                'nome_cientifico': ponto.planta.nome_cientifico,
            }
        form = PontoPANCForm(instance=ponto, initial=initial)
    plantas = PlantaReferencial.objects.order_by('nome_popular')
    return render(request, 'mapping/cadastrar_ponto.html', {
        'form': form,
        'plantas': plantas,
        'edicao': True,
        'ponto': ponto,
    })


@login_required

def reverse_geocode(request):
    
    lat = request.GET.get("lat")
    lng = request.GET.get("lng")

    try:
        url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lng}&addressdetails=1"
        headers = {"User-Agent": "ColaboraPANC"}
        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status()
        return JsonResponse(response.json())
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)

@login_required
def remover_ponto(request, pk):
    ponto = get_object_or_404(PontoPANC, pk=pk)
    if ponto.colaborador != request.user.username and not request.user.is_superuser:
        messages.error(request, "Você não tem permissão para remover este ponto.")
        return redirect('painel_contribuicoes')
    ponto.delete()
    messages.success(request, "Ponto removido com sucesso!")
    return redirect("painel_contribuicoes")


# =======================
# AUTOCOMPLETE E API DE APOIO
# =======================

@login_required
def buscar_nome_cientifico(request):
    nome = request.GET.get('nome_popular', '').strip()
    resolved = _resolver_nome_cientifico_por_sugestao(nome)
    return JsonResponse(resolved)

@login_required
def autocomplete_nome_popular(request):
    termo = request.GET.get('term', '').strip().lower()
    detalhado = request.GET.get("detailed", "").lower() in {"1", "true", "sim", "yes"}
    sugestoes = _montar_sugestoes_nomes_populares(termo, limite=10)
    if detalhado:
        return JsonResponse(sugestoes, safe=False)
    return JsonResponse([item["nome_popular"] for item in sugestoes], safe=False)

# =======================
# API DE IDENTIFICAÇÃO AUTOMÁTICA
# =======================

@csrf_exempt
@login_required
def api_identificar(request):
    if request.method == "POST" and request.FILES.get("foto"):
        foto = request.FILES['foto']
        identificacao = plant_identification_service.identify(foto=foto)
        resultados = identificacao.candidatos or []
        if not resultados:
            resultados = identificar_planta_api(foto)
        if not isinstance(resultados, list):
            resultados = [{'erro': 'Resposta inesperada da API de identificação.'}]
        return JsonResponse(resultados, safe=False)
    return JsonResponse([{'erro': 'Método não suportado ou foto ausente.'}], safe=False, status=400)

@login_required
def teste_identificacao(request):
    return render(request, 'mapping/teste_identificacao.html')

# =======================
# VALIDAÇÃO (ESPECIALISTA/REVISOR)
# =======================

@login_required
@user_passes_test(is_revisor)
def painel_validacao(request):
    pontos = (
        PontoPANC.objects.filter(status_validacao='pendente')
        .exclude(pareceres__especialista=request.user)
        .order_by('-criado_em')
    )
    return render(request, 'mapping/painel_validacao.html', {'pontos': pontos})

@login_required
@user_passes_test(is_revisor)
def validar_ponto(request, ponto_id):
    ponto = get_object_or_404(PontoPANC, id=ponto_id)
    if request.method == "POST":
        parecer = request.POST.get('parecer')
        comentario = request.POST.get('comentario', '')
        ParecerValidacao.objects.create(
            ponto=ponto,
            especialista=request.user,
            parecer=parecer,
            comentario=comentario
        )
        pareceres = ParecerValidacao.objects.filter(ponto=ponto)
        aprovados = pareceres.filter(parecer='aprovado').count()
        reprovados = pareceres.filter(parecer='reprovado').count()
        pendencias = pareceres.filter(parecer='pendencia').count()
        if aprovados >= 2:
            ponto.status_validacao = 'aprovado'
        elif reprovados >= 2:
            ponto.status_validacao = 'reprovado'
        elif pendencias >= 1:
            ponto.status_validacao = 'pendencia'
        ponto.save()
        messages.success(request, "Parecer registrado com sucesso!")
        registrar_acao_gamificada(request.user, 'revisao')

        return redirect('painel_validacao')
    return render(request, 'mapping/validar_ponto.html', {'ponto': ponto})

# =======================
# GRUPOS / COMUNIDADES
# =======================

@login_required
def painel_grupos(request):
    grupos = Grupo.objects.filter(membros=request.user)
    return render(request, 'mapping/painel_grupos.html', {'grupos': grupos})

# =======================
# GAMIFICAÇÃO / CONQUISTAS
# =======================

@login_required
def minhas_conquistas(request):
    badges_usuario = UsuarioBadge.objects.filter(usuario=request.user)
    return render(request, 'mapping/minhas_conquistas.html', {'badges': badges})

def conquistas_disponiveis(request):
    # Esqueleto para evitar erro caso view esteja só no urls.py
    return render(request, 'mapping/conquistas_disponiveis.html')

def ranking_usuarios(request):
    # Esqueleto para evitar erro caso view esteja só no urls.py
    return render(request, 'mapping/ranking_usuarios.html')

def historico_gamificacao(request):
    # Esqueleto para evitar erro caso view esteja só no urls.py
    return render(request, 'mapping/historico_gamificacao.html')

# =======================
# FEEDBACK
# =======================

@login_required
def enviar_feedback(request):
    if request.method == 'POST':
        mensagem = request.POST.get('mensagem', '').strip()
        ponto_id = request.POST.get('ponto_id')
        ponto = PontoPANC.objects.filter(id=ponto_id).first() if ponto_id else None
        Feedback.objects.create(usuario=request.user, mensagem=mensagem, ponto=ponto)
        # Pontuação feedback
        adicionar_pontos(request.user, 2, "Enviou Feedback")
        messages.success(request, "Feedback enviado com sucesso!")
        return redirect('obrigado')
    return render(request, 'mapping/enviar_feedback.html')



@login_required
def lista_feedbacks(request):
    feedbacks = Feedback.objects.all().order_by('-criado_em')
    return render(request, 'mapping/lista_feedbacks.html', {'feedbacks': feedbacks})

def obrigado(request):
    # View simples de agradecimento pós-feedback
    return render(request, 'mapping/obrigado.html')



# =======================
# LISTA DE COMUNIDADES / GRUPOS
# =======================

def lista_comunidades(request):
    grupos = Grupo.objects.all()
    return render(request, 'mapping/lista_comunidades.html', {'grupos': grupos})
    
@login_required
def meus_grupos(request):
    grupos = Grupo.objects.filter(membros=request.user)
    return render(request, 'mapping/meus_grupos.html', {'grupos': grupos})    
    

# =============================
# Painel Principal de Gamificação
# =============================
@login_required
def painel_gamificacao(request):
    usuario = request.user

    # Pontuação e nível do usuário (garante existência)
    pontuacao = PontuacaoUsuario.objects.get_or_create(usuario=usuario)[0]

    # Badges conquistados pelo usuário (mais recentes primeiro)
    badges_usuario = UsuarioBadge.objects.filter(usuario=usuario).select_related('badge').order_by('-data_conquista')

    # Missões ativas e separação entre pendentes/concluídas
    missoes_ativas = Missao.objects.filter(ativa=True)
    missoes_usuario = MissaoUsuario.objects.filter(usuario=usuario)
    concluidas = missoes_ativas.filter(
        id__in=missoes_usuario.filter(completada=True).values_list('missao_id', flat=True)
    )
    pendentes = missoes_ativas.exclude(
        id__in=missoes_usuario.filter(completada=True).values_list('missao_id', flat=True)
    )

    # Top 10 usuários por pontuação
    ranking_usuarios = PontuacaoUsuario.objects.select_related('usuario').order_by('-pontos')[:10]

    # Histórico de gamificação do usuário (últimas 20 ações)
    historico = HistoricoGamificacao.objects.filter(usuario=usuario).order_by('-data')[:20]

    # Botão flutuante de ação especial ou notificação (se houver)
    botao_flutuante = BotaoFlutuante.objects.filter(usuario=usuario, exibido=True).first()

    # Contexto para o template
    context = {
        "pontuacao": pontuacao,
        "badges_usuario": badges_usuario,
        "pendentes": pendentes,
        "concluidas": concluidas,
        "ranking_usuarios": ranking_usuarios,
        "historico": historico,
        "botao_flutuante": botao_flutuante,
    }
    return render(request, "mapping/painel_gamificacao.html", context)
# =============================
# Minhas Conquistas
# =============================
@login_required
def minhas_conquistas(request):
    # Recupera as conquistas (badges) do usuário usando a tabela intermediária UsuarioBadge
    conquistas = UsuarioBadge.objects.filter(usuario=request.user).select_related('badge').order_by('-data_conquista')
    pontuacao = PontuacaoUsuario.objects.get_or_create(usuario=request.user)[0]
    return render(request, "mapping/minhas_conquistas.html", {
        "conquistas": conquistas,
        "pontuacao": pontuacao
    })
# =============================
# Ranking Geral de Usuários
# =============================
@login_required
def ranking_usuarios(request):
    ranking = PontuacaoUsuario.objects.select_related('usuario').order_by('-pontos', '-nivel')[:100]
    ranking_revisores = RankingRevisor.objects.select_related('usuario').order_by('-pontuacao', '-avaliacoes')[:50]
    return render(request, "mapping/ranking_usuarios.html", {
        "ranking": ranking,
        "ranking_revisores": ranking_revisores,
    })

# =============================
# Conquistas Disponíveis
# =============================
@login_required
def conquistas_disponiveis(request):
    todas_badges = Badge.objects.values('nome', 'descricao', 'icone').distinct()
    return render(request, "mapping/conquistas_disponiveis.html", {"badges": todas_badges})

# =============================
# Histórico de Gamificação
# =============================
@login_required
def historico_gamificacao(request):
    historico = HistoricoGamificacao.objects.filter(usuario=request.user).order_by('-data')[:100]
    return render(request, "mapping/historico_gamificacao.html", {"historico": historico})

# =============================
# Missões: listar, calcular progresso, concluir e sugerir
# =============================
from django.utils import timezone

@login_required
def missoes(request):
    usuario = request.user
    hoje = timezone.now().date()
    semana_atual = hoje - timezone.timedelta(days=7)

    def get_progresso(missao, usuario):
        # Cálculo automático por tipo
        if missao.tipo == 'diaria':
            progresso = PontoPANC.objects.filter(colaborador=usuario.username, criado_em__date=hoje).count()
        elif missao.tipo == 'semanal':
            progresso = PontoPANC.objects.filter(colaborador=usuario.username, criado_em__date__gte=semana_atual).count()
        elif missao.tipo == 'meta':
            progresso = PontoPANC.objects.filter(colaborador=usuario.username).count()
        elif missao.tipo == 'especial' and 'feedback' in missao.titulo.lower():
            progresso = Feedback.objects.filter(usuario=usuario).count()
        else:
            progresso = 0
        meta = missao.meta or 1
        return progresso, meta

    missoes_ativas = Missao.objects.filter(ativa=True)
    missoes_diarias, missoes_semanais, missoes_especiais = [], [], []

    for m in missoes_ativas:
        progresso, meta = get_progresso(m, usuario)
        completa = progresso >= meta

        # Atualiza ou cria progresso da missão para o usuário
        mu, _ = MissaoUsuario.objects.get_or_create(usuario=usuario, missao=m)
        mu.progresso = progresso
        mu.completa = completa
        if completa and not mu.data_conclusao:
            mu.data_conclusao = timezone.now()
        mu.save()

        missao_dict = {
            'id': m.id,
            'titulo': m.titulo,
            'descricao': m.descricao,
            'tipo': m.tipo,
            'pontos': m.pontos,
            'meta': meta,
            'progresso': progresso,
            'progresso_percent': min(100, int(100 * progresso / meta)) if meta else 100,
            'completa': completa,
            'secreta': m.secreta,
        }
        if m.tipo == 'diaria':
            missoes_diarias.append(missao_dict)
        elif m.tipo == 'semanal':
            missoes_semanais.append(missao_dict)
        else:
            missoes_especiais.append(missao_dict)

    ctx = {
        'missoes_diarias': missoes_diarias,
        'missoes_semanais': missoes_semanais,
        'missoes_especiais': missoes_especiais,
    }
    return render(request, "mapping/missoes.html", ctx)


@login_required
def concluir_missao(request, missao_id):
    missao = get_object_or_404(Missao, id=missao_id, ativa=True)
    mu, created = MissaoUsuario.objects.get_or_create(usuario=request.user, missao=missao)
    if not mu.completa:
        mu.completa = True
        mu.data_conclusao = timezone.now()
        mu.save()
        # Pontuação
        pontuacao = PontuacaoUsuario.objects.get_or_create(usuario=request.user)[0]
        pontuacao.pontos += missao.pontos
        pontuacao.atualizar_nivel()
        HistoricoGamificacao.objects.create(
            usuario=request.user,
            acao=f"Missão concluída: {missao.titulo}",
            pontos=missao.pontos,
            referencia=f"Missao:{missao.id}"
        )
        messages.success(request, "Missão concluída! Pontos adicionados.")
    return redirect("missoes")


@login_required
def sugerir_missao(request):
    if request.method == "POST":
        form = SugestaoMissaoForm(request.POST)
        if form.is_valid():
            sugestao = form.save(commit=False)
            sugestao.usuario = request.user
            sugestao.save()
            messages.success(request, "Sugestão de missão enviada para análise!")
            return redirect("missoes")
    else:
        form = SugestaoMissaoForm()
    return render(request, "mapping/sugerir_missao.html", {"form": form})


# =============================
# Botão flutuante: apagar ao subir de nível
# =============================
@login_required
def apagar_botao_flutuante(request):
    BotaoFlutuante.objects.filter(usuario=request.user).delete()
    return JsonResponse({"ok": True})

@login_required
def remover_botao_flutuante(request):
    if request.method == "POST":
        BotaoFlutuante.objects.filter(usuario=request.user).delete()
        return JsonResponse({"status": "removido"})
    return JsonResponse({"erro": "Requisição inválida"}, status=400)
    
# =============================
# Painel de Administração de Gamificação
# =============================

@login_required
def painel_admin_gamificacao(request):
    # KPIs
    total_usuarios = User.objects.count()
    total_pontos = PontuacaoUsuario.objects.aggregate(Sum('pontos'))['pontos__sum'] or 0
    total_missoes_concluidas = HistoricoGamificacao.objects.filter(acao__icontains="Missão concluída").count()
    total_badges = Badge.objects.count()
    total_sugestoes = SugestaoMissao.objects.count()
    kpis = [
        {"titulo": "Usuários ativos", "valor": total_usuarios, "icone": "bi bi-person-fill", "cor": "info"},
        {"titulo": "Pontos distribuídos", "valor": total_pontos, "icone": "bi bi-coin", "cor": "warning"},
        {"titulo": "Missões concluídas", "valor": total_missoes_concluidas, "cor": "success", "icone": "bi bi-stars"},
        {"titulo": "Conquistas atribuídas", "valor": total_badges, "icone": "bi bi-trophy", "cor": "primary"},
        {"titulo": "Sugestões recebidas", "valor": total_sugestoes, "icone": "bi bi-chat-dots", "cor": "secondary"},
    ]

    # Gráficos e Mapa
    cadastros_labels, cadastros_data = get_cadastros_mensais()
    top_usuarios_labels, top_usuarios_data = get_top_usuarios()
    pontos_geojson = json.dumps(pontos_to_geojson())

    # Últimos registros
    historico = HistoricoGamificacao.objects.select_related('usuario').order_by('-data')[:20]
    missoes_recent = Missao.objects.order_by('-data_criacao')[:6]
    conquistas_recent = Badge.objects.order_by('-data_criacao')[:6]  # <<=== Corrigido aqui!
    feedbacks_recent = Feedback.objects.order_by('-criado_em')[:6]

    # Rankings
    ranking_usuarios = PontuacaoUsuario.objects.select_related('usuario').order_by('-pontos')[:10]
    ranking_revisores = RankingRevisor.objects.order_by('-pontuacao')[:10]

    # Sugestões
    sugestoes = SugestaoMissao.objects.all().order_by('-criado_em')[:10]

    return render(request, "mapping/painel_admin_gamificacao.html", {
        "kpis": kpis,
        "historico": historico,
        "missoes_recent": missoes_recent,
        "conquistas_recent": conquistas_recent,
        "feedbacks_recent": feedbacks_recent,
        "cadastros_labels": json.dumps(cadastros_labels),
        "cadastros_data": json.dumps(cadastros_data),
        "top_usuarios_labels": json.dumps(top_usuarios_labels),
        "top_usuarios_data": json.dumps(top_usuarios_data),
        "pontos_geojson": pontos_geojson,
        "ranking_usuarios": ranking_usuarios,
        "ranking_revisores": ranking_revisores,
        "sugestoes": sugestoes,
        "total_badges": total_badges,
        "total_missoes": Missao.objects.filter(ativa=True).count(),
        "total_usuarios": total_usuarios,
        "total_sugestoes": total_sugestoes,
    })

# =============================
# Funções auxiliares para outras lógicas
# =============================
# ...exemplo de uso:
def atualizar_pontuacao_ao_realizar_acao(usuario, pontos, acao, referencia=''):
    pontuacao = PontuacaoUsuario.objects.get_or_create(usuario=usuario)[0]
    pontuacao.pontos += pontos
    pontuacao.atualizar_nivel()
    HistoricoGamificacao.objects.create(
        usuario=usuario,
        acao=acao,
        pontos=pontos,
        referencia=referencia
    )
 
# =============================
# Ranking Revisor
# =============================

@login_required
@user_passes_test(lambda u: u.is_superuser or u.groups.filter(name='Revisores').exists())
def ranking_revisores(request):
    ranking = RankingRevisor.objects.order_by('-pontuacao')[:50]  # Ajuste o campo de pontuação conforme seu model
    return render(request, 'mapping/ranking_revisores.html', {'ranking': ranking})
    
    
    
@user_passes_test(lambda u: u.is_superuser)
def criar_missao(request):
    # Sua lógica para criar missão (formulário, etc)
    return render(request, "mapping/criar_missao.html")    

# =============================
# Conquista Criar
# =============================

@login_required
@user_passes_test(lambda u: u.is_superuser)
def criar_conquista(request):
    if request.method == "POST":
        nome = request.POST.get('nome', '').strip()
        descricao = request.POST.get('descricao', '').strip()
        username = request.POST.get('usuario', '').strip()

        usuario = None
        if username:
            from django.contrib.auth.models import User
            usuario = User.objects.filter(username=username).first()

        if nome and descricao:
            Badge.objects.create(
                nome=nome,
                descricao=descricao,
                usuario=usuario
            )
            messages.success(request, "Conquista criada/atribuída com sucesso!")
            return redirect('painel_admin_gamificacao')  # ajuste para sua URL principal do painel
        else:
            messages.error(request, "Preencha todos os campos obrigatórios.")

    return redirect('painel_admin_gamificacao')
    
@login_required
def painel_admin_gamificacao(request):
    # Indicadores (exemplo)
    total_usuarios = User.objects.count()
    total_pontos = PontuacaoUsuario.objects.aggregate(Sum('pontos'))['pontos__sum'] or 0
    total_missoes_concluidas = HistoricoGamificacao.objects.filter(acao__icontains="Missão concluída").count()
    total_badges = Badge.objects.count()
    # total_grupos = ... # coloque sua consulta de grupos aqui

    kpis = [
        {"titulo": "Usuários ativos", "valor": total_usuarios, "icone": "bi bi-person-fill", "cor": "info"},
        {"titulo": "Pontos distribuídos", "valor": total_pontos, "icone": "bi bi-coin", "cor": "warning"},
        {"titulo": "Missões concluídas", "valor": total_missoes_concluidas, "cor": "success", "icone": "bi bi-stars"},
        {"titulo": "Conquistas atribuídas", "valor": total_badges, "icone": "bi bi-trophy", "cor": "primary"},
    ]

    # Dados para gráficos (preencha conforme sua função utilitária)
    cadastros_labels, cadastros_data = get_cadastros_mensais()
    top_usuarios_labels, top_usuarios_data = get_top_usuarios()
    pontos_geojson = pontos_to_geojson()

    # Últimas ações/itens
    historico = HistoricoGamificacao.objects.select_related('usuario').order_by('-data')[:20]
    missoes_recent = Missao.objects.order_by('-data_criacao')[:6]
    conquistas_recent = Badge.objects.order_by('-data_criacao')[:6]
    feedbacks_recent = Feedback.objects.order_by('-criado_em')[:6]

    return render(request, "mapping/painel_admin_gamificacao.html", {
        "kpis": kpis,
        "historico": historico,
        "missoes_recent": missoes_recent,
        "conquistas_recent": conquistas_recent,
        "feedbacks_recent": feedbacks_recent,
        "cadastros_labels": cadastros_labels,
        "cadastros_data": cadastros_data,
        "top_usuarios_labels": top_usuarios_labels,
        "top_usuarios_data": top_usuarios_data,
        "pontos_geojson": pontos_geojson,
    })


# =============================
# CRUD Missões
# =============================

@user_passes_test(lambda u: u.is_superuser)
def criar_missao(request):
    if request.method == "POST":
        titulo = request.POST.get('titulo', '').strip()
        descricao = request.POST.get('descricao', '').strip()
        tipo = request.POST.get('tipo', 'especial')
        pontos = int(request.POST.get('pontos', 1))
        ativa = bool(request.POST.get('ativa', False))
        if titulo and descricao:
            Missao.objects.create(
                titulo=titulo,
                descricao=descricao,
                tipo=tipo,
                pontos=pontos,
                ativa=ativa,
            )
            messages.success(request, "Missão criada com sucesso!")
        else:
            messages.error(request, "Preencha todos os campos obrigatórios.")
    return redirect('painel_admin_gamificacao')

@user_passes_test(lambda u: u.is_superuser)
def editar_missao(request, missao_id):
    missao = get_object_or_404(Missao, id=missao_id)
    if request.method == "POST":
        missao.titulo = request.POST.get('titulo', missao.titulo)
        missao.descricao = request.POST.get('descricao', missao.descricao)
        missao.tipo = request.POST.get('tipo', missao.tipo)
        missao.pontos = int(request.POST.get('pontos', missao.pontos))
        missao.ativa = bool(request.POST.get('ativa', missao.ativa))
        missao.save()
        messages.success(request, "Missão atualizada com sucesso!")
        return redirect('painel_admin_gamificacao')
    return render(request, "mapping/editar_missao.html", {"missao": missao})

@user_passes_test(lambda u: u.is_superuser)
def excluir_missao(request, missao_id):
    missao = get_object_or_404(Missao, id=missao_id)
    missao.delete()
    messages.success(request, "Missão excluída com sucesso!")
    return redirect('painel_admin_gamificacao')

@user_passes_test(lambda u: u.is_superuser)
def desativar_missao(request, missao_id):
    missao = get_object_or_404(Missao, id=missao_id)
    missao.ativa = not missao.ativa
    missao.save()
    status = "ativada" if missao.ativa else "desativada"
    messages.success(request, f"Missão {status} com sucesso!")
    return redirect('painel_admin_gamificacao')

# =============================
# CRUD Conquistas (Badges)
# =============================

@user_passes_test(lambda u: u.is_superuser)
def criar_conquista(request):
    if request.method == "POST":
        nome = request.POST.get('nome', '').strip()
        descricao = request.POST.get('descricao', '').strip()
        username = request.POST.get('usuario', '').strip()
        icone = request.FILES.get('icone')
        usuario = User.objects.filter(username=username).first() if username else None
        if nome and descricao:
            Badge.objects.create(
                nome=nome,
                descricao=descricao,
                usuario=usuario,
                icone=icone,
            )
            messages.success(request, "Conquista criada/atribuída com sucesso!")
        else:
            messages.error(request, "Preencha todos os campos obrigatórios.")
    return redirect('painel_admin_gamificacao')

@user_passes_test(lambda u: u.is_superuser)
def editar_conquista(request, badge_id):
    badge = get_object_or_404(Badge, id=badge_id)
    if request.method == "POST":
        badge.nome = request.POST.get('nome', badge.nome)
        badge.descricao = request.POST.get('descricao', badge.descricao)
        username = request.POST.get('usuario', badge.usuario.username if badge.usuario else '')
        badge.usuario = User.objects.filter(username=username).first() if username else None
        if request.FILES.get('icone'):
            badge.icone = request.FILES.get('icone')
        badge.save()
        messages.success(request, "Conquista atualizada com sucesso!")
        return redirect('painel_admin_gamificacao')
    return render(request, "mapping/editar_conquista.html", {"badge": badge})

@user_passes_test(lambda u: u.is_superuser)
def excluir_conquista(request, badge_id):
    badge = get_object_or_404(Badge, id=badge_id)
    badge.delete()
    messages.success(request, "Conquista excluída com sucesso!")
    return redirect('painel_admin_gamificacao')

# =============================
# Feedbacks - Admin View
# =============================

@user_passes_test(lambda u: u.is_superuser)
def admin_lista_feedbacks(request):
    feedbacks = Feedback.objects.all().order_by('-criado_em')
    return render(request, 'mapping/admin_lista_feedbacks.html', {'feedbacks': feedbacks})



# =============================
# Exportação de Relatórios
# =============================

@user_passes_test(lambda u: u.is_superuser)
def exportar_relatorio(request):
    # Exemplo: exportar pontos para CSV
    import csv
    from django.http import HttpResponse

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="pontos_panc.csv"'
    writer = csv.writer(response)
    writer.writerow(['ID', 'Nome Popular', 'Nome Científico', 'Cidade', 'Estado', 'Data'])

    for p in PontoPANC.objects.all():
        writer.writerow([p.id, p.planta.nome_popular if p.planta else '', p.planta.nome_cientifico if p.planta else '', p.cidade, p.estado, p.criado_em])

    return response



# =============================
# GAMIFICAÇÃO COLABORATIVA USUÁRIO (MELHORADA)
# =============================


@login_required
def criar_missao_usuario(request):
    if request.method == 'POST':
        titulo = request.POST.get('titulo', '').strip()
        descricao = request.POST.get('descricao', '').strip()
        pontos = int(request.POST.get('pontos', 1))
        pontos = min(pontos, 100)
        tipo = request.POST.get('tipo', 'especial')
        if pontos_disponiveis_para_criador(request.user) >= pontos:
            missao = Missao.objects.create(
                titulo=titulo,
                descricao=descricao,
                tipo=tipo,
                pontos=pontos,
                ativa=True,
                criador=request.user
            )
            adicionar_pontos(request.user, pontos, "Criou Desafio", f"Missao:{missao.id}")
            messages.success(request, "Missão criada!")
            return redirect('minhas_missoes')
        else:
            messages.error(request, "Limite diário de pontos para criação de desafios atingido (100 pontos).")
    return render(request, 'mapping/criar_missao_usuario.html')


@login_required
def minhas_missoes(request):
    """
    Mostra as missões criadas pelo usuário logado.
    """
    minhas = Missao.objects.filter(criador=request.user).order_by('-data_criacao')
    return render(request, "mapping/minhas_missoes.html", {"minhas": minhas})


@login_required
def missoes_colaborativas(request):
    """
    Lista todas as missões colaborativas (ativas) e status do usuário.
    """
    missoes_ativas = Missao.objects.filter(ativa=True)
    # Todos os objetos MissaoUsuario do usuário (participação e conclusão)
    minhas_missao_usuario = MissaoUsuario.objects.filter(usuario=request.user)
    minhas_concluidas_map = {mu.missao_id: mu for mu in minhas_missao_usuario if mu.completada}
    minhas_participacoes_ids = [mu.missao_id for mu in minhas_missao_usuario]
    # Separar pendentes das concluídas (pelo usuário)
    pendentes = missoes_ativas.exclude(id__in=minhas_concluidas_map.keys())
    concluidas_info = []
    for mu in minhas_concluidas_map.values():
        concluidas_info.append({
            "missao": mu.missao,
            "data_conclusao": mu.data_conclusao,
            "pontos": mu.missao.pontos,
            "criador": mu.missao.criador,
        })
    return render(request, "mapping/missoes_colaborativas.html", {
        "pendentes": pendentes,
        "concluidas_info": concluidas_info,
        "minhas_participacoes_ids": minhas_participacoes_ids,  # útil para "botão Participar" desabilitar
    })


@login_required
def participar_missao(request, missao_id):
    """
    Usuário entra em uma missão colaborativa para participar.
    """
    missao = get_object_or_404(Missao, id=missao_id, ativa=True)
    mu, created = MissaoUsuario.objects.get_or_create(usuario=request.user, missao=missao)
    if created:
        messages.success(request, f"Você agora participa da missão '{missao.titulo}'!")
    else:
        messages.info(request, "Você já está participando desta missão.")
    return redirect('missoes_colaborativas')



@login_required
def concluir_missao_usuario(request, missao_id):
    missao = get_object_or_404(Missao, id=missao_id, ativa=True)
    mu, created = MissaoUsuario.objects.get_or_create(usuario=request.user, missao=missao)
    if not mu.completada:
        mu.completada = True
        mu.data_conclusao = timezone.now()
        mu.save()
        # Pontuação automática (usar valor definido na missão)
        adicionar_pontos(request.user, missao.pontos, f"Concluiu Missão: {missao.titulo}", f"Missao:{missao.id}")
        messages.success(request, "Missão concluída! Pontos adicionados.")
    return redirect("missoes_colaborativas")

@login_required
def ranking_missao(request, missao_id):
    """
    Mostra o ranking de usuários que completaram determinada missão colaborativa.
    """
    missao = get_object_or_404(Missao, id=missao_id)
    ranking = (
        MissaoUsuario.objects.filter(missao=missao, completada=True)
        .select_related('usuario')
        .order_by('data_conclusao')  # Os primeiros a concluir aparecem no topo
    )
    return render(request, "mapping/ranking_missao.html", {
        "missao": missao,
        "ranking": ranking
    })


# =============================
# Gráficos do painel
# =============================

def get_cadastros_mensais():
    # Últimos 6 meses
    hoje = datetime.now()
    labels = []
    data = []
    for i in range(5, -1, -1):
        mes = hoje - timedelta(days=30*i)
        nome_mes = calendar.month_abbr[mes.month]
        labels.append(f'{nome_mes}/{mes.year}')
        data.append(
            User.objects.filter(date_joined__year=mes.year, date_joined__month=mes.month).count()
        )
    return labels, data

def get_top_usuarios():
    top_usuarios = PontuacaoUsuario.objects.select_related('usuario').order_by('-pontos')[:10]
    labels = [u.usuario.username for u in top_usuarios]
    data = [u.pontos for u in top_usuarios]
    return labels, data

def pontos_to_geojson():
    # Retorna os pontos como GeoJSON para o mapa (pode usar serializers, exemplo simplificado abaixo)
    pontos = PontoPANC.objects.all()
    features = []
    for p in pontos:
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [p.localizacao.x, p.localizacao.y]
            },
            "properties": {
                "nome": p.nome_popular,
                "cidade": p.cidade,
            }
        })
    return {
        "type": "FeatureCollection",
        "features": features,
    }
# =============================
# Exportação de CSV
# =============================

@login_required
def exportar_usuarios_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="usuarios.csv"'
    writer = csv.writer(response)
    writer.writerow(['ID', 'Usuário', 'E-mail', 'Data de cadastro', 'Pontos'])
    for u in User.objects.all():
        pontuacao = getattr(u, 'pontuacao', None)
        pontos = pontuacao.pontos if pontuacao else 0
        writer.writerow([u.id, u.username, u.email, u.date_joined, pontos])
    return response

@login_required
def exportar_pontos_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="pontos_panc.csv"'
    writer = csv.writer(response)
    writer.writerow(['ID', 'Nome popular', 'Cidade', 'Estado', 'Latitude', 'Longitude', 'Criado por'])
    for p in PontoPANC.objects.all():
        writer.writerow([
            p.id, p.nome_popular, p.cidade, p.estado, p.localizacao.y, p.localizacao.x,
            p.criado_por.username if p.criado_por else '-'
        ])
    return response

# =============================
# Alerta climático - views.py
# =============================

from django.shortcuts import render
from .models import AlertaClimatico, PontoPANC, EventoMonitorado
from .serializers import PontoPANCSerializer
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView, DeleteView
from rest_framework import viewsets, generics

# View para exibir o histórico/ lista de alertas
def lista_alertas(request):
    """
    Exibe uma lista filtrável de todos os alertas climáticos registrados no sistema.
    Os filtros disponíveis são: estado, nome popular do ponto e tipo de alerta.
    A lista é ordenada por data de início em ordem decrescente.
    """
    estado = request.GET.get("estado")
    ponto = request.GET.get("ponto")
    tipo = request.GET.get("tipo")

    alertas = AlertaClimatico.objects.select_related('ponto').all()

    if estado:
        alertas = alertas.filter(ponto__estado__icontains=estado)
    if ponto:
        alertas = alertas.filter(ponto__nome_popular__icontains=ponto)
    if tipo:
        alertas = alertas.filter(tipo__icontains=tipo)

    alertas = alertas.order_by('-inicio')

    return render(request, 'mapping/lista_alertas.html', {
        'alertas': alertas,
        'estado': estado or '',
        'ponto': ponto or '',
        'tipo': tipo or '',
    })


class PontoPANCViewSet(viewsets.ModelViewSet):
    queryset = PontoPANC.objects.select_related("planta", "grupo").prefetch_related(
        Prefetch(
            "alertas",
            queryset=AlertaClimatico.objects.order_by("-inicio"),
            to_attr="alertas_ordenados",
        ),
        Prefetch(
            "eventos_monitorados",
            queryset=EventoMonitorado.objects.order_by("-ocorrido_em"),
            to_attr="eventos_monitorados_ordenados",
        ),
        "historico_enriquecimento",
    )
    serializer_class = PontoPANCSerializer

    def list(self, request, *args, **kwargs):
        queryset = aplicar_filtros_pontos(request, self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        data = request.data if hasattr(request, "data") else {}

        localizacao = data.get("localizacao")
        if isinstance(localizacao, str):
            bruto = localizacao.strip()
            if bruto:
                try:
                    localizacao = json.loads(bruto)
                except json.JSONDecodeError:
                    if "," in bruto:
                        partes = [p.strip() for p in bruto.split(",")]
                        if len(partes) == 2:
                            localizacao = [partes[0], partes[1]]
        if localizacao in (None, "", "null"):
            lon_raw = data.get("longitude")
            lat_raw = data.get("latitude")
            if lon_raw is not None and lat_raw is not None:
                localizacao = [lon_raw, lat_raw]
        longitude = latitude = None

        if isinstance(localizacao, (list, tuple)) and len(localizacao) == 2:
            longitude, latitude = localizacao[0], localizacao[1]
        elif isinstance(localizacao, dict):
            if isinstance(localizacao.get("coordinates"), (list, tuple)) and len(localizacao["coordinates"]) == 2:
                longitude, latitude = localizacao["coordinates"][0], localizacao["coordinates"][1]
            elif "longitude" in localizacao and "latitude" in localizacao:
                longitude, latitude = localizacao["longitude"], localizacao["latitude"]

        try:
            longitude = float(longitude)
            latitude = float(latitude)
        except (TypeError, ValueError):
            return Response({"erro": "Localização inválida para cadastro do ponto."}, status=status.HTTP_400_BAD_REQUEST)

        if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
            return Response({"erro": "Coordenadas fora da faixa permitida."}, status=status.HTTP_400_BAD_REQUEST)

        nome_popular = (data.get("nome_popular") or "").strip()
        nome_cientifico = (data.get("nome_cientifico") or "").strip()
        nome_cientifico_sugerido = (data.get("nome_cientifico_sugerido") or "").strip()
        nome_cientifico_escolhido = (data.get("nome_cientifico_escolhido") or "").strip()
        nome_cientifico_final = nome_cientifico_escolhido or nome_cientifico or nome_cientifico_sugerido
        if not nome_cientifico_final:
            resolved = _resolver_nome_cientifico_por_sugestao(nome_popular)
            nome_cientifico_final = resolved.get("nome_cientifico", "")
        if not nome_popular:
            return Response({"erro": "Nome popular é obrigatório."}, status=status.HTTP_400_BAD_REQUEST)

        planta = None
        planta_id = data.get("planta_id")
        if planta_id:
            planta = PlantaReferencial.objects.filter(id=planta_id).first()
        if not planta:
            planta = canonical_store.find_existing(
                scientific_name=nome_cientifico_final,
                popular_name=nome_popular,
                aliases=[nome_cientifico_final, nome_popular, nome_cientifico_sugerido],
            )
        if not planta and nome_cientifico_final:
            planta = PlantaReferencial.objects.filter(nome_cientifico__iexact=nome_cientifico_final).first()
        if not planta:
            planta = PlantaReferencial.objects.filter(nome_popular__iexact=nome_popular).first()
        if not planta:
            planta = PlantaReferencial.objects.create(
                nome_popular=nome_popular[:200],
                nome_cientifico=nome_cientifico_final[:200],
            )

        tipo_local = (data.get("tipo_local") or "outro").strip().lower()
        tipos_validos = {choice[0] for choice in TIPOS_DE_LOCAL}
        if tipo_local not in tipos_validos:
            tipo_local = "outro"

        colaborador = (
            getattr(request.user, "username", "")
            if getattr(request.user, "is_authenticated", False)
            else (data.get("colaborador") or "")
        )

        ponto = PontoPANC(
            planta=planta,
            nome_popular=nome_popular[:500],
            tipo_local=tipo_local,
            colaborador=(colaborador or "")[:255],
            relato=(data.get("relato") or "")[:5000],
            cidade=(data.get("cidade") or "")[:255],
            estado=(data.get("estado") or "")[:255],
            criado_por=request.user if getattr(request.user, "is_authenticated", False) else None,
            localizacao=Point(longitude, latitude, srid=4326),
            latitude=latitude,
            longitude=longitude,
            status_fluxo='submetido',
            nome_cientifico_submetido=nome_cientifico_final[:200] if nome_cientifico_final else None,
        )
        _apply_manual_food_fields_to_ponto(ponto, payload=data)
        ponto.full_clean(exclude=['foto'])
        ponto.save()
        _sync_manual_fields_to_planta(ponto)

        if (data.get("enriquecer_automaticamente", True) not in [False, "false", "0", 0]):
            try:
                logger.info("Disparando enriquecimento automático no cadastro do ponto=%s", ponto.id)
                plant_enrichment_pipeline.run_for_ponto(
                    ponto,
                    include_trefle=True,
                    origem="cadastro",
                )
            except Exception as exc:
                logger.warning("Enriquecimento parcial no cadastro do ponto %s: %s", ponto.id, exc)
                ponto.status_enriquecimento = "parcial"
                ponto.save(update_fields=["status_enriquecimento", "atualizado_em"])

        logger.debug("Serializando resposta de criação do ponto=%s", ponto.id)
        serializer = self.get_serializer(ponto)
        logger.info("Resposta cadastro ponto=%s status=%s enriquecimento=%s", ponto.id, status.HTTP_201_CREATED, ponto.status_enriquecimento)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        ponto = self.get_object()
        _apply_manual_food_fields_to_ponto(ponto, payload=request.data)
        _sync_manual_fields_to_planta(ponto)
        ponto.save()
        if request.data.get("revalidar_taxonomia", True) in [True, "true", "1", 1]:
            try:
                logger.info("Disparando revalidação taxonômica no update do ponto=%s", ponto.id)
                plant_enrichment_pipeline.run_for_ponto(
                    ponto,
                    include_trefle=True,
                    origem="edicao",
                )
            except Exception as exc:
                logger.warning("Falha na revalidação de enriquecimento %s: %s", ponto.id, exc)
        logger.debug("Serializando resposta de atualização do ponto=%s", ponto.id)
        serializer = self.get_serializer(ponto)
        logger.info("Resposta update ponto=%s status=%s enriquecimento=%s", ponto.id, response.status_code, ponto.status_enriquecimento)
        return Response(serializer.data, status=response.status_code)

    @action(detail=True, methods=["post"], url_path="enriquecimento")
    def enriquecimento(self, request, pk=None):
        ponto = self.get_object()
        logger.info("Requisição manual de enriquecimento recebida para ponto=%s", ponto.id)
        result = plant_enrichment_pipeline.run_for_ponto(ponto, include_trefle=True, origem="manual")
        logger.info("Resposta enriquecimento manual ponto=%s ok=%s status=%s", ponto.id, result.get("ok"), result.get("status_enriquecimento"))
        return Response(result, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="revalidar")
    def revalidar(self, request, pk=None):
        ponto = self.get_object()
        result = plant_enrichment_pipeline.run_for_ponto(ponto, include_trefle=False, origem="revalidacao_manual")
        return Response(result, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"], url_path="revalidar-lote")
    def revalidar_lote(self, request):
        ids = request.data.get("ids") or []
        queryset = self.get_queryset()
        if ids:
            queryset = queryset.filter(id__in=ids)
        limite = int(request.data.get("limite", 50) or 50)
        pontos = list(queryset.order_by("-atualizado_em")[:limite])
        resultados = []
        for ponto in pontos:
            try:
                resultados.append({"ponto_id": ponto.id, **plant_enrichment_pipeline.run_for_ponto(ponto, include_trefle=False, origem="revalidacao_lote")})
            except Exception as exc:
                resultados.append({"ponto_id": ponto.id, "ok": False, "error": str(exc)})
        return Response({"total": len(resultados), "resultados": resultados}, status=status.HTTP_200_OK)

class PontoPANCListAPIView(generics.ListAPIView):
    queryset = PontoPANC.objects.all()
    serializer_class = PontoPANCSerializer


class NotificacaoViewSet(viewsets.ModelViewSet):
    queryset = Notificacao.objects.all()
    serializer_class = NotificacaoSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        usuario_id = self.request.query_params.get("usuario_id")
        if self.request.user.is_authenticated:
            return queryset.filter(usuario=self.request.user)
        if usuario_id:
            return queryset.filter(usuario_id=usuario_id)
        return queryset.none()


class ConversaViewSet(viewsets.ModelViewSet):
    queryset = Conversa.objects.prefetch_related("participantes", "mensagens")
    serializer_class = ConversaSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        usuario_id = self.request.query_params.get("usuario_id")
        if self.request.user.is_authenticated:
            return queryset.filter(participantes=self.request.user)
        if usuario_id:
            return queryset.filter(participantes__id=usuario_id)
        return queryset.none()


class MensagemViewSet(viewsets.ModelViewSet):
    queryset = Mensagem.objects.select_related("remetente", "conversa")
    serializer_class = MensagemSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        conversa_id = self.request.query_params.get("conversa_id")
        if conversa_id:
            return queryset.filter(conversa_id=conversa_id)
        return queryset.none()


class CompartilhamentoSocialViewSet(viewsets.ModelViewSet):
    queryset = CompartilhamentoSocial.objects.select_related("ponto", "usuario")
    serializer_class = CompartilhamentoSocialSerializer


class RecomendacaoPANCViewSet(viewsets.ModelViewSet):
    queryset = RecomendacaoPANC.objects.select_related("usuario", "planta")
    serializer_class = RecomendacaoPANCSerializer


class IntegracaoEcommerceViewSet(viewsets.ModelViewSet):
    queryset = IntegracaoEcommerce.objects.all()
    serializer_class = IntegracaoEcommerceSerializer


class ProdutoSementeViewSet(viewsets.ModelViewSet):
    queryset = ProdutoSemente.objects.select_related("integracao", "planta")
    serializer_class = ProdutoSementeSerializer


class RoteiroPANCViewSet(viewsets.ModelViewSet):
    queryset = RoteiroPANC.objects.select_related("criador").prefetch_related("itens")
    serializer_class = RoteiroPANCSerializer


class RoteiroPANCItemViewSet(viewsets.ModelViewSet):
    queryset = RoteiroPANCItem.objects.select_related("roteiro", "ponto")
    serializer_class = RoteiroPANCItemSerializer


class ReferenciaARViewSet(viewsets.ModelViewSet):
    queryset = ReferenciaAR.objects.select_related("planta")
    serializer_class = ReferenciaARSerializer

class AlertaCreateView(CreateView):
    model = AlertaClimatico
    fields = [
        'ponto', 'tipo', 'severidade', 'descricao', 'inicio', 'fim',
        'municipio', 'uf', 'id_alerta', 'fonte', 'icone'
    ]
    template_name = 'alertas/alerta_form.html'
    success_url = reverse_lazy('mapa_colaborativo')

class AlertaUpdateView(UpdateView):
    model = AlertaClimatico
    fields = [
        'ponto', 'tipo', 'severidade', 'descricao', 'inicio', 'fim',
        'municipio', 'uf', 'id_alerta', 'fonte', 'icone'
    ]
    template_name = 'alertas/alerta_form.html'
    success_url = reverse_lazy('mapa_colaborativo')

class AlertaDeleteView(DeleteView):
    model = AlertaClimatico
    template_name = 'alertas/alerta_confirm_delete.html'
    success_url = reverse_lazy('mapa_colaborativo')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['alerta'] = self.object
        return context

# =============================
# Alerta Manuais - views.py
# =============================


def mapa(request):
    """
    Exibe o mapa principal com todos os pontos e seus alertas associados.
    """
    pontos = PontoPANC.objects.prefetch_related('alertas').all()
    return render(request, 'mapping/mapa.html', {'pontos': pontos})

def alerta_novo(request):
    pontos = PontoPANC.objects.all().order_by('estado', 'cidade')
    if request.method == "POST":
        ponto_id = request.POST.get('ponto')
        tipo = request.POST.get('tipo')
        inicio = request.POST.get('inicio')
        fim = request.POST.get('fim')
        descricao = request.POST.get('descricao', '')

        alerta = AlertaClimatico(
            ponto_id=ponto_id,
            tipo=tipo,
            inicio=inicio,
            fim=fim,
            descricao=descricao,
            fonte="manual",
        )
        alerta.save()
        messages.success(request, "Alerta salvo com sucesso!")
        return redirect('lista_alertas')
    return render(request, "alertas/alerta_form.html", {"pontos": pontos})

# =============================
# Aplicativo
# =============================

def mapa_app(request):
    return render(request, 'mapping/mapa-app.html')
    
# =============================
# Aplicativo - autenticação
# =============================  

@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
def api_login(request):
    username = request.data.get('username') or request.data.get('email')
    password = request.data.get('password')
    user = authenticate(username=username, password=password)
    if user:
        django_login(request, user)
        token, _ = Token.objects.get_or_create(user=user)
        return Response(
            {
                'detail': 'Login OK',
                'token': token.key,
                'user_id': user.id,
                'username': user.username,
            },
            status=status.HTTP_200_OK
        )
    return Response({'detail': 'Credenciais inválidas'}, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
def api_register(request):
    nome = (request.data.get('nome') or '').strip()
    email = (request.data.get('email') or '').strip().lower()
    password = request.data.get('password')

    if not nome or not email or not password:
        return Response({'detail': 'Nome, email e senha são obrigatórios.'}, status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(email__iexact=email).exists():
        return Response({'detail': 'Este email já está em uso.'}, status=status.HTTP_400_BAD_REQUEST)

    base_username = email.split('@')[0] or 'usuario'
    username = base_username
    suffix = 1
    while User.objects.filter(username=username).exists():
        suffix += 1
        username = f'{base_username}{suffix}'

    user = User.objects.create_user(
        username=username,
        first_name=nome,
        email=email,
        password=password,
    )
    django_login(request, user)
    token, _ = Token.objects.get_or_create(user=user)
    return Response(
        {
            'detail': 'Conta criada com sucesso.',
            'token': token.key,
            'user_id': user.id,
            'username': user.username,
        },
        status=status.HTTP_201_CREATED
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_user_profile(request):
    """Retorna dados do perfil do usuário logado"""
    user = request.user
    pontos_count = PontoPANC.objects.filter(criado_por=user).count()
    from .models import UsuarioBadge, PontuacaoUsuario
    badges_count = UsuarioBadge.objects.filter(usuario=user).count()
    try:
        pontuacao_obj = PontuacaoUsuario.objects.get(usuario=user)
        pontuacao = pontuacao_obj.pontos
        nivel = pontuacao_obj.nivel.nome if pontuacao_obj.nivel else ''
    except Exception:
        pontuacao = 0
        nivel = ''

    return Response({
        'id': user.id,
        'username': user.username,
        'nome': user.first_name or user.username,
        'email': user.email,
        'date_joined': user.date_joined.isoformat() if user.date_joined else '',
        'pontos_cadastrados': pontos_count,
        'badges_count': badges_count,
        'pontuacao': pontuacao,
        'nivel': nivel,
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_change_password(request):
    """Altera a senha do usuário logado"""
    user = request.user
    senha_atual = request.data.get('senha_atual', '')
    nova_senha = request.data.get('nova_senha', '')

    if not senha_atual or not nova_senha:
        return Response({'detail': 'Senha atual e nova senha são obrigatórias.'}, status=status.HTTP_400_BAD_REQUEST)

    if not user.check_password(senha_atual):
        return Response({'detail': 'Senha atual incorreta.'}, status=status.HTTP_400_BAD_REQUEST)

    if len(nova_senha) < 6:
        return Response({'detail': 'Nova senha deve ter pelo menos 6 caracteres.'}, status=status.HTTP_400_BAD_REQUEST)

    user.set_password(nova_senha)
    user.save()

    # Regenerate token
    Token.objects.filter(user=user).delete()
    token = Token.objects.create(user=user)

    return Response({
        'detail': 'Senha alterada com sucesso.',
        'token': token.key,
    })


@api_view(["POST"])
def registrar_push_token(request):
    token = request.data.get("token")
    plataforma = request.data.get("plataforma", "outro")
    usuario_id = request.data.get("usuario_id")

    if not token:
        return Response({"detail": "Token obrigatório."}, status=status.HTTP_400_BAD_REQUEST)

    usuario = request.user if request.user.is_authenticated else None
    if not usuario and usuario_id:
        usuario = get_object_or_404(User, pk=usuario_id)
    if not usuario:
        return Response({"detail": "Usuário não encontrado."}, status=status.HTTP_400_BAD_REQUEST)

    registro, _ = DispositivoPush.objects.update_or_create(
        token=token,
        defaults={"usuario": usuario, "plataforma": plataforma, "ativo": True},
    )

    serializer = DispositivoPushSerializer(registro)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["GET", "POST"])
def api_notificacoes(request):
    if request.method == "POST":
        notificacao_id = request.data.get("id")
        if notificacao_id:
            notificacao = get_object_or_404(Notificacao, pk=notificacao_id)
            notificacao.lida_em = timezone.now()
            notificacao.save(update_fields=["lida_em"])
            return Response(NotificacaoSerializer(notificacao).data)

        usuario_id = request.data.get("usuario_id")
        usuario = request.user if request.user.is_authenticated else None
        if not usuario and usuario_id:
            usuario = get_object_or_404(User, pk=usuario_id)
        if not usuario:
            return Response({"detail": "Usuário obrigatório."}, status=status.HTTP_400_BAD_REQUEST)

        notificacao = Notificacao.objects.create(
            usuario=usuario,
            titulo=request.data.get("titulo", "Atualização ColaboraPANC"),
            mensagem=request.data.get("mensagem", ""),
            dados=request.data.get("dados", {}),
        )
        return Response(NotificacaoSerializer(notificacao).data, status=status.HTTP_201_CREATED)

    usuario_id = request.query_params.get("usuario_id")
    queryset = Notificacao.objects.all()
    if request.user.is_authenticated:
        queryset = queryset.filter(usuario=request.user)
    elif usuario_id:
        queryset = queryset.filter(usuario_id=usuario_id)
    else:
        queryset = queryset.none()
    return Response(NotificacaoSerializer(queryset, many=True).data)


@api_view(["GET", "POST"])
def api_conversas(request):
    if request.method == "POST":
        participantes_ids = request.data.get("participantes", [])
        if not participantes_ids:
            return Response({"detail": "Participantes obrigatórios."}, status=status.HTTP_400_BAD_REQUEST)
        conversa = Conversa.objects.create()
        conversa.participantes.set(User.objects.filter(id__in=participantes_ids))
        conversa.save()
        return Response(ConversaSerializer(conversa).data, status=status.HTTP_201_CREATED)

    usuario_id = request.query_params.get("usuario_id")
    queryset = Conversa.objects.prefetch_related("participantes", "mensagens")
    if request.user.is_authenticated:
        queryset = queryset.filter(participantes=request.user)
    elif usuario_id:
        queryset = queryset.filter(participantes__id=usuario_id)
    else:
        queryset = queryset.none()
    return Response(ConversaSerializer(queryset, many=True).data)


@api_view(["GET", "POST"])
def api_mensagens(request):
    if request.method == "POST":
        conversa_id = request.data.get("conversa_id")
        remetente_id = request.data.get("remetente_id")
        conteudo = request.data.get("conteudo") or request.data.get("texto")
        if not (conversa_id and remetente_id and conteudo):
            return Response({"detail": "Conversa, remetente e texto são obrigatórios."}, status=status.HTTP_400_BAD_REQUEST)
        conversa = get_object_or_404(Conversa, pk=conversa_id)
        remetente = get_object_or_404(User, pk=remetente_id)
        mensagem = Mensagem.objects.create(conversa=conversa, remetente=remetente, conteudo=conteudo)
        conversa.save(update_fields=["atualizada_em"])
        return Response(MensagemSerializer(mensagem).data, status=status.HTTP_201_CREATED)

    conversa_id = request.query_params.get("conversa_id")
    mensagens = Mensagem.objects.select_related("remetente", "conversa")
    if conversa_id:
        mensagens = mensagens.filter(conversa_id=conversa_id)
    else:
        mensagens = mensagens.none()
    return Response(MensagemSerializer(mensagens, many=True).data)


@api_view(["POST"])
def api_compartilhamento(request):
    ponto_id = request.data.get("ponto_id")
    canal = request.data.get("canal", "outro")
    url_compartilhada = request.data.get("url_compartilhada", "")
    usuario_id = request.data.get("usuario_id")

    if not ponto_id:
        return Response({"detail": "Ponto obrigatório."}, status=status.HTTP_400_BAD_REQUEST)

    usuario = request.user if request.user.is_authenticated else None
    if not usuario and usuario_id:
        usuario = get_object_or_404(User, pk=usuario_id)

    compartilhamento = CompartilhamentoSocial.objects.create(
        usuario=usuario,
        ponto_id=ponto_id,
        canal=canal,
        url_compartilhada=url_compartilhada,
    )
    return Response(CompartilhamentoSocialSerializer(compartilhamento).data, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def atualizar_recomendacoes(request):
    from .services.recomendacao_ml import (
        atualizar_recomendacoes_usuario,
        atualizar_recomendacoes_todos_usuarios,
    )

    atualizar_todos = request.data.get("todos") or request.query_params.get("todos")
    if atualizar_todos and request.user.is_superuser:
        atualizar_recomendacoes_todos_usuarios()
        return Response({"status": "recomendacoes_atualizadas", "escopo": "todos"})

    recomendacoes = atualizar_recomendacoes_usuario(request.user)
    return Response({
        "status": "recomendacoes_atualizadas",
        "escopo": "usuario",
        "quantidade": len(recomendacoes),
    })


@api_view(["GET"])
def api_offline_sync(request):
    since_param = request.query_params.get("since")
    since = parse_datetime(since_param) if since_param else None
    if since and timezone.is_naive(since):
        since = timezone.make_aware(since, timezone.get_current_timezone())

    pontos = PontoPANC.objects.select_related("planta", "grupo").prefetch_related(
        Prefetch(
            "alertas",
            queryset=AlertaClimatico.objects.order_by("-inicio"),
            to_attr="alertas_ordenados",
        ),
        Prefetch(
            "eventos_monitorados",
            queryset=EventoMonitorado.objects.order_by("-ocorrido_em"),
            to_attr="eventos_monitorados_ordenados",
        ),
    )
    if since:
        pontos = pontos.filter(criado_em__gte=since)

    paginator = PageNumberPagination()
    paginator.page_size = int(request.query_params.get("page_size", 200))
    paginator.page_size_query_param = "page_size"
    paginator.max_page_size = 500
    pontos_paginados = paginator.paginate_queryset(pontos, request)

    plantas = PlantaReferencial.objects.all()
    pontos_serializados = []
    for ponto in pontos_paginados:
        serializado = serializar_ponto_api(ponto)
        if serializado:
            pontos_serializados.append(serializado)
    data = {
        "pontos": pontos_serializados,
        "pontos_paginacao": {
            "count": paginator.page.paginator.count,
            "next": paginator.get_next_link(),
            "previous": paginator.get_previous_link(),
        },
        "plantas": list(plantas.values("id", "nome_popular", "nome_cientifico", "bioma", "origem", "regiao_ocorrencia")),
        "since": since_param,
        "gerado_em": timezone.now().isoformat(),
    }
    return Response(data)


def _get_request_value(request, key, default=None):
    if request.method == "GET":
        return request.query_params.get(key, default)
    return request.data.get(key, default)


@api_view(["POST"])
def calcular_rota(request):
    pontos_data = request.data if isinstance(request.data, list) else request.data.get("pontos")
    if not pontos_data:
        return Response(
            {"detail": "Lista de pontos obrigatória."},
            status=status.HTTP_400_BAD_REQUEST
        )

    pontos = []
    for index, item in enumerate(pontos_data):
        if not isinstance(item, dict):
            continue
        ponto_id = item.get("id") or item.get("ponto_id")
        lat = item.get("lat") or item.get("latitude")
        lng = item.get("lng") or item.get("longitude")

        if (lat is None or lng is None) and ponto_id:
            ponto = PontoPANC.objects.filter(id=ponto_id, localizacao__isnull=False).first()
            if ponto and ponto.localizacao:
                lat = ponto.localizacao.y
                lng = ponto.localizacao.x

        try:
            lat = float(lat) if lat is not None else None
            lng = float(lng) if lng is not None else None
        except (TypeError, ValueError):
            lat = None
            lng = None

        if lat is None or lng is None:
            continue

        pontos.append({
            "id": ponto_id or index + 1,
            "lat": lat,
            "lng": lng,
        })

    if not pontos:
        return Response(
            {"detail": "Nenhum ponto válido informado."},
            status=status.HTTP_400_BAD_REQUEST
        )

    resultado = rotas_service.calcular_rota_otimizada(pontos)
    return Response(resultado)


@api_view(["GET"])
def pontos_proximos(request):
    latitude = _get_request_value(request, "lat")
    longitude = _get_request_value(request, "lng")
    if latitude is None or longitude is None:
        return Response(
            {"detail": "Latitude e longitude são obrigatórias."},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        latitude = float(latitude)
        longitude = float(longitude)
        raio_km = float(_get_request_value(request, "raio_km", 10))
        limite = int(_get_request_value(request, "limite", 10))
    except (TypeError, ValueError):
        return Response(
            {"detail": "Parâmetros inválidos para localização."},
            status=status.HTTP_400_BAD_REQUEST
        )

    pontos = rotas_service.obter_pontos_proximos(
        latitude=latitude,
        longitude=longitude,
        raio_km=raio_km,
        limite=limite
    )
    return Response({"pontos": pontos, "total": len(pontos)})


@api_view(["GET", "POST"])
def sugerir_rota_automatica(request):
    latitude = _get_request_value(request, "lat")
    longitude = _get_request_value(request, "lng")
    if latitude is None or longitude is None:
        return Response(
            {"detail": "Latitude e longitude são obrigatórias."},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        latitude = float(latitude)
        longitude = float(longitude)
        num_pontos = int(_get_request_value(request, "num_pontos", 5))
        raio_km = float(_get_request_value(request, "raio_km", 20))
    except (TypeError, ValueError):
        return Response(
            {"detail": "Parâmetros inválidos para localização."},
            status=status.HTTP_400_BAD_REQUEST
        )

    resultado = rotas_service.sugerir_rota_automatica(
        latitude=latitude,
        longitude=longitude,
        num_pontos=num_pontos,
        raio_km=raio_km
    )
    return Response(resultado)
