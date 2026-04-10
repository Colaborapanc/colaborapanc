# mapping/views_api.py
# Views da API REST para as novas funcionalidades

from rest_framework import viewsets, generics, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db import transaction
from datetime import timedelta
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count, Prefetch, Avg
from django.utils import timezone

from .models import (
    Notificacao, DispositivoPush, Conversa, Mensagem,
    RecomendacaoPANC, LojaExterno, ProdutoExterno,
    Rota, RotaPonto, PreferenciasUsuario, PlantaReferencial,
    PontoPANC, AlertaClimatico, PredicaoIA, ValidacaoEspecialista,
    HistoricoValidacao
)
from .serializers import (
    NotificacaoSerializer, DispositivoPushSerializer,
    ConversaSerializer, MensagemSerializer,
    RecomendacaoPANCSerializer, LojaExternoSerializer,
    ProdutoExternoSerializer, RotaSerializer,
    PreferenciasUsuarioSerializer, PlantaReferencialSerializer,
    PontoPANCSerializer, PredicaoIASerializer, ValidacaoEspecialistaSerializer,
    HistoricoValidacaoSerializer
)

from .services.ia_identificacao import identificar_com_multiplos_provedores
from .services.priorizacao_territorial import calcular_score_prioridade
from .permissions import IsReviewerOrAdmin

# ===================================
# VIEWSETS - NOTIFICAÇÕES
# ===================================
class NotificacaoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciar notificações do usuário
    """
    serializer_class = NotificacaoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Notificacao.objects.filter(usuario=self.request.user)

    @action(detail=False, methods=['get'])
    def nao_lidas(self, request):
        """Retorna apenas notificações não lidas"""
        nao_lidas = self.get_queryset().filter(lida=False)
        serializer = self.get_serializer(nao_lidas, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def marcar_lida(self, request, pk=None):
        """Marca uma notificação como lida"""
        notificacao = self.get_object()
        notificacao.marcar_como_lida()
        return Response({'status': 'marcada como lida'})

    @action(detail=False, methods=['post'])
    def marcar_todas_lidas(self, request):
        """Marca todas as notificações como lidas"""
        self.get_queryset().filter(lida=False).update(
            lida=True,
            lida_em=timezone.now()
        )
        return Response({'status': 'todas marcadas como lidas'})

    @action(detail=False, methods=['get'])
    def contador(self, request):
        """Retorna contagem de notificações não lidas"""
        count = self.get_queryset().filter(lida=False).count()
        return Response({'nao_lidas': count})


class DispositivoPushViewSet(viewsets.ModelViewSet):
    """
    ViewSet para registrar dispositivos para notificações push
    """
    serializer_class = DispositivoPushSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return DispositivoPush.objects.filter(usuario=self.request.user)

    def create(self, request, *args, **kwargs):
        """Registra ou atualiza token de dispositivo"""
        token = request.data.get('token')
        plataforma = request.data.get('plataforma')

        if not token or not plataforma:
            return Response(
                {'error': 'Token e plataforma são obrigatórios'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Verifica se o token já existe
        dispositivo, created = DispositivoPush.objects.update_or_create(
            token=token,
            defaults={
                'usuario': request.user,
                'plataforma': plataforma,
                'ativo': True
            }
        )

        serializer = self.get_serializer(dispositivo)
        status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response(serializer.data, status=status_code)

    @action(detail=True, methods=['post'])
    def desativar(self, request, pk=None):
        """Desativa um dispositivo"""
        dispositivo = self.get_object()
        dispositivo.ativo = False
        dispositivo.save()
        return Response({'status': 'dispositivo desativado'})


# ===================================
# VIEWSETS - MENSAGENS
# ===================================
class ConversaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciar conversas entre usuários
    """
    serializer_class = ConversaSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Conversa.objects.filter(
            participantes=self.request.user
        ).prefetch_related('participantes', 'mensagens')

    def create(self, request, *args, **kwargs):
        """Cria uma nova conversa ou retorna existente"""
        outro_usuario_id = request.data.get('outro_usuario_id')

        if not outro_usuario_id:
            return Response(
                {'error': 'outro_usuario_id é obrigatório'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Verifica se já existe uma conversa entre os dois
        conversa = Conversa.objects.filter(
            participantes=request.user
        ).filter(
            participantes__id=outro_usuario_id
        ).first()

        if conversa:
            serializer = self.get_serializer(conversa)
            return Response(serializer.data)

        # Cria nova conversa
        conversa = Conversa.objects.create()
        conversa.participantes.add(request.user, outro_usuario_id)

        serializer = self.get_serializer(conversa)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class MensagemViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciar mensagens em conversas
    """
    serializer_class = MensagemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        conversa_id = self.request.query_params.get('conversa_id')
        if conversa_id:
            return Mensagem.objects.filter(
                conversa__id=conversa_id,
                conversa__participantes=self.request.user
            )
        return Mensagem.objects.filter(
            conversa__participantes=self.request.user
        )

    def create(self, request, *args, **kwargs):
        """Envia uma nova mensagem"""
        conversa_id = request.data.get('conversa_id')
        conteudo = request.data.get('conteudo')

        if not conversa_id or not conteudo:
            return Response(
                {'error': 'conversa_id e conteudo são obrigatórios'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Verifica se o usuário participa da conversa
        conversa = get_object_or_404(
            Conversa,
            id=conversa_id,
            participantes=request.user
        )

        mensagem = Mensagem.objects.create(
            conversa=conversa,
            remetente=request.user,
            conteudo=conteudo
        )

        # Cria notificação para o outro participante
        outro_participante = conversa.get_outro_participante(request.user)
        if outro_participante:
            Notificacao.objects.create(
                usuario=outro_participante,
                tipo='mensagem',
                titulo='Nova mensagem',
                mensagem=f'{request.user.username} enviou uma mensagem',
                link=f'/conversas/{conversa.id}'
            )

        serializer = self.get_serializer(mensagem)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def marcar_lida(self, request, pk=None):
        """Marca uma mensagem como lida"""
        mensagem = self.get_object()
        if mensagem.remetente != request.user:
            mensagem.marcar_como_lida()
            return Response({'status': 'marcada como lida'})
        return Response(
            {'error': 'Não pode marcar própria mensagem como lida'},
            status=status.HTTP_400_BAD_REQUEST
        )


# ===================================
# VIEWSETS - RECOMENDAÇÕES
# ===================================
class RecomendacaoPANCViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para visualizar recomendações personalizadas de PANCs
    """
    serializer_class = RecomendacaoPANCSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return RecomendacaoPANC.objects.filter(
            usuario=self.request.user
        ).select_related('planta')

    @action(detail=True, methods=['post'])
    def marcar_visualizada(self, request, pk=None):
        """Marca recomendação como visualizada"""
        recomendacao = self.get_object()
        recomendacao.visualizada = True
        recomendacao.save()
        return Response({'status': 'marcada como visualizada'})


# ===================================
# VIEWSETS - E-COMMERCE
# ===================================
class LojaExternoViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para listar lojas parceiras
    """
    queryset = LojaExterno.objects.filter(ativo=True)
    serializer_class = LojaExternoSerializer
    permission_classes = [AllowAny]


class ProdutoExternoViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para listar produtos disponíveis
    """
    serializer_class = ProdutoExternoSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        queryset = ProdutoExterno.objects.filter(
            disponivel=True,
            loja__ativo=True
        ).select_related('loja', 'planta')

        # Filtros opcionais
        planta_id = self.request.query_params.get('planta_id')
        loja_id = self.request.query_params.get('loja_id')

        if planta_id:
            queryset = queryset.filter(planta_id=planta_id)
        if loja_id:
            queryset = queryset.filter(loja_id=loja_id)

        return queryset


# ===================================
# VIEWSETS - ROTAS
# ===================================
class RotaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciar rotas de PANCs
    """
    serializer_class = RotaSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Usuário vê suas próprias rotas + rotas públicas
        return Rota.objects.filter(
            Q(usuario=self.request.user) | Q(publica=True)
        ).select_related('usuario').prefetch_related('pontos')

    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user)

    @action(detail=True, methods=['post'])
    def adicionar_ponto(self, request, pk=None):
        """Adiciona um ponto à rota"""
        rota = self.get_object()

        # Verifica permissão
        if rota.usuario != request.user:
            return Response(
                {'error': 'Sem permissão para editar esta rota'},
                status=status.HTTP_403_FORBIDDEN
            )

        ponto_id = request.data.get('ponto_id')
        if not ponto_id:
            return Response(
                {'error': 'ponto_id é obrigatório'},
                status=status.HTTP_400_BAD_REQUEST
            )

        ponto = get_object_or_404(PontoPANC, id=ponto_id)

        # Determina a próxima ordem
        ultima_ordem = RotaPonto.objects.filter(rota=rota).aggregate(
            max_ordem=Count('ordem')
        )['max_ordem'] or 0

        RotaPonto.objects.create(
            rota=rota,
            ponto=ponto,
            ordem=ultima_ordem + 1
        )

        serializer = self.get_serializer(rota)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def marcar_visitado(self, request, pk=None):
        """Marca um ponto da rota como visitado"""
        rota = self.get_object()
        ponto_rota_id = request.data.get('ponto_rota_id')

        if not ponto_rota_id:
            return Response(
                {'error': 'ponto_rota_id é obrigatório'},
                status=status.HTTP_400_BAD_REQUEST
            )

        ponto_rota = get_object_or_404(RotaPonto, id=ponto_rota_id, rota=rota)
        ponto_rota.visitado = True
        ponto_rota.data_visita = timezone.now()
        ponto_rota.save()

        return Response({'status': 'ponto marcado como visitado'})


# ===================================
# VIEWSETS - PREFERÊNCIAS
# ===================================
class PreferenciasUsuarioViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciar preferências do usuário
    """
    serializer_class = PreferenciasUsuarioSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return PreferenciasUsuario.objects.filter(usuario=self.request.user)

    def get_object(self):
        """Retorna ou cria preferências do usuário"""
        obj, created = PreferenciasUsuario.objects.get_or_create(
            usuario=self.request.user
        )
        return obj

    def list(self, request, *args, **kwargs):
        """Retorna preferências do usuário"""
        preferencias = self.get_object()
        serializer = self.get_serializer(preferencias)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        """Atualiza preferências do usuário"""
        preferencias = self.get_object()
        serializer = self.get_serializer(preferencias, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


# ===================================
# API - BUSCA AVANÇADA
# ===================================
@api_view(['GET'])
@permission_classes([AllowAny])
def busca_avancada_pontos(request):
    """
    Busca avançada de pontos PANC com múltiplos filtros
    """
    queryset = PontoPANC.objects.select_related("planta", "grupo").prefetch_related(
        Prefetch(
            "alertas",
            queryset=AlertaClimatico.objects.order_by("-inicio"),
            to_attr="alertas_ordenados",
        )
    )

    # Filtros
    nome = request.GET.get('nome')
    cidade = request.GET.get('cidade')
    estado = request.GET.get('estado')
    tipo_local = request.GET.get('tipo_local')
    planta_id = request.GET.get('planta_id')
    status_validacao = request.GET.get('status_validacao')
    grupo_id = request.GET.get('grupo_id')

    # Filtros geográficos (bounding box)
    lat_min = request.GET.get('lat_min')
    lat_max = request.GET.get('lat_max')
    lng_min = request.GET.get('lng_min')
    lng_max = request.GET.get('lng_max')

    if nome:
        queryset = queryset.filter(
            Q(nome_popular__icontains=nome) |
            Q(planta__nome_popular__icontains=nome) |
            Q(planta__nome_cientifico__icontains=nome)
        )

    if cidade:
        queryset = queryset.filter(cidade__icontains=cidade)

    if estado:
        queryset = queryset.filter(estado__iexact=estado)

    if tipo_local:
        queryset = queryset.filter(tipo_local=tipo_local)

    if planta_id:
        queryset = queryset.filter(planta_id=planta_id)

    if status_validacao:
        queryset = queryset.filter(status_validacao=status_validacao)

    if grupo_id:
        queryset = queryset.filter(grupo_id=grupo_id)

    # Filtro geográfico (bounding box)
    if all([lat_min, lat_max, lng_min, lng_max]):
        queryset = queryset.filter(
            latitude__gte=float(lat_min),
            latitude__lte=float(lat_max),
            longitude__gte=float(lng_min),
            longitude__lte=float(lng_max)
        )

    paginator = PageNumberPagination()
    paginator.page_size = int(request.GET.get("page_size", 20))
    paginator.page_size_query_param = "page_size"
    paginator.max_page_size = 200
    pontos = paginator.paginate_queryset(queryset, request)

    serializer = PontoPANCSerializer(pontos, many=True)

    return paginator.get_paginated_response(serializer.data)


# ===================================
# API - PLANTAS REFERENCIAIS
# ===================================
@api_view(['GET'])
@permission_classes([AllowAny])
def listar_plantas(request):
    """
    Lista todas as plantas referenciais com filtros
    """
    queryset = PlantaReferencial.objects.all()

    # Filtros
    nome = request.GET.get('nome')
    bioma = request.GET.get('bioma')
    origem = request.GET.get('origem')

    if nome:
        queryset = queryset.filter(
            Q(nome_popular__icontains=nome) |
            Q(nome_cientifico__icontains=nome)
        )

    if bioma:
        queryset = queryset.filter(bioma__icontains=bioma)

    if origem:
        queryset = queryset.filter(origem__icontains=origem)

    serializer = PlantaReferencialSerializer(queryset, many=True)
    return Response(serializer.data)



class InferenciaPontoAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, ponto_id):
        ponto = get_object_or_404(PontoPANC, id=ponto_id)
        if not ponto.foto:
            return Response({'detail': 'Ponto sem imagem para inferência.'}, status=status.HTTP_400_BAD_REQUEST)

        if hasattr(ponto.foto, 'file') and getattr(ponto.foto.file, 'content_type', ''):
            if not ponto.foto.file.content_type.startswith('image/'):
                return Response({'detail': 'Arquivo de imagem inválido.'}, status=status.HTTP_400_BAD_REQUEST)

        resultado = identificar_com_multiplos_provedores(
            ponto.foto,
            plantid_api_key=request.headers.get('X-PLANTID-KEY', ''),
        )
        if not resultado:
            return Response({'detail': 'Nenhum provedor de IA retornou predição.'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        with transaction.atomic():
            pred = PredicaoIA.objects.create(
                ponto=ponto,
                provedor=resultado.provedor,
                predicoes_top_k=resultado.top_k,
                score_confianca=resultado.score,
                faixa_risco=resultado.faixa_risco,
                justificativa=resultado.justificativa,
                requer_revisao_humana=resultado.requer_revisao_humana,
                fonte_predicao=resultado.fonte_predicao,
            )
            ponto.status_fluxo = 'em_revisao' if resultado.requer_revisao_humana else 'submetido'
            ponto.nome_popular_sugerido = (resultado.top_k[0].get('nome_popular') or '')[:100]
            ponto.nome_cientifico_sugerido = (resultado.top_k[0].get('nome_cientifico') or '')[:150]
            ponto.score_identificacao = resultado.score * 100
            ponto.status_identificacao = 'sugerido'
            ponto.save(update_fields=['status_fluxo', 'nome_popular_sugerido', 'nome_cientifico_sugerido', 'score_identificacao', 'status_identificacao', 'atualizado_em'])

            HistoricoValidacao.objects.create(
                ponto=ponto,
                usuario=request.user,
                evento='predicao_ia_gerada',
                dados={'provedor': resultado.provedor, 'score': resultado.score, 'faixa_risco': resultado.faixa_risco},
            )

        return Response(PredicaoIASerializer(pred).data, status=status.HTTP_201_CREATED)


class FilaRevisaoAPIView(generics.ListAPIView):
    permission_classes = [IsReviewerOrAdmin]
    serializer_class = PontoPANCSerializer

    def get_queryset(self):
        qs = PontoPANC.objects.filter(status_fluxo__in=['submetido', 'em_revisao', 'necessita_revisao']).order_by('-criado_em')
        confianca = self.request.query_params.get('confianca')
        status_fluxo = self.request.query_params.get('status_fluxo')
        dias = self.request.query_params.get('dias')
        if confianca == 'alta':
            qs = qs.filter(score_identificacao__gte=85)
        elif confianca == 'media':
            qs = qs.filter(score_identificacao__gte=60, score_identificacao__lt=85)
        elif confianca == 'baixa':
            qs = qs.filter(score_identificacao__lt=60)

        if status_fluxo in {'submetido','em_revisao','necessita_revisao'}:
            qs = qs.filter(status_fluxo=status_fluxo)

        if dias and str(dias).isdigit():
            limite = timezone.now() - timedelta(days=int(dias))
            qs = qs.filter(criado_em__gte=limite)
        return qs


class ValidacaoPontoAPIView(APIView):
    permission_classes = [IsReviewerOrAdmin]

    def post(self, request, ponto_id):
        ponto = get_object_or_404(PontoPANC, id=ponto_id)
        decisao = request.data.get('decisao_final')
        if decisao not in {'validado', 'rejeitado', 'necessita_revisao'}:
            return Response({'detail': 'decisao_final inválida.'}, status=status.HTTP_400_BAD_REQUEST)

        predicao = ponto.predicoes_ia.order_by('-criado_em').first()
        with transaction.atomic():
            registro = ValidacaoEspecialista.objects.create(
                ponto=ponto,
                revisor=request.user,
                predicao_ia=predicao,
                decisao_final=decisao,
                especie_final=request.data.get('especie_final', ''),
                motivo_divergencia=request.data.get('motivo_divergencia', ''),
                observacao=request.data.get('observacao', ''),
            )

            ponto.status_fluxo = decisao
            ponto.status_validacao = 'aprovado' if decisao == 'validado' else ('reprovado' if decisao == 'rejeitado' else 'pendencia')
            ponto.save(update_fields=['status_fluxo', 'status_validacao', 'atualizado_em'])

            HistoricoValidacao.objects.create(
                ponto=ponto,
                usuario=request.user,
                evento='validacao_humana',
                dados={
                    'decisao_final': decisao,
                    'predicao_id': predicao.id if predicao else None,
                    'motivo_divergencia': request.data.get('motivo_divergencia', ''),
                },
            )

        return Response(ValidacaoEspecialistaSerializer(registro).data, status=status.HTTP_201_CREATED)


class DetalheRevisaoPontoAPIView(APIView):
    permission_classes = [IsReviewerOrAdmin]

    def get(self, request, ponto_id):
        ponto = get_object_or_404(PontoPANC, id=ponto_id)
        predicao = ponto.predicoes_ia.order_by('-criado_em').first()
        ultima_validacao = ponto.validacoes_especialistas.order_by('-criado_em').first()
        return Response({
            'ponto': PontoPANCSerializer(ponto, context={'request': request}).data,
            'predicao_ia': PredicaoIASerializer(predicao).data if predicao else None,
            'ultima_validacao': ValidacaoEspecialistaSerializer(ultima_validacao).data if ultima_validacao else None,
            'historico': HistoricoValidacaoSerializer(ponto.historico_validacoes.all()[:20], many=True).data,
        })


class HistoricoDecisoesAPIView(generics.ListAPIView):
    permission_classes = [IsReviewerOrAdmin]
    serializer_class = HistoricoValidacaoSerializer

    def get_queryset(self):
        ponto_id = self.kwargs['ponto_id']
        return HistoricoValidacao.objects.filter(ponto_id=ponto_id).select_related('usuario').order_by('-criado_em')


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_analitico(request):
    pontos = PontoPANC.objects.all()
    total = pontos.count()
    validados = pontos.filter(status_fluxo='validado').count()
    rejeitados = pontos.filter(status_fluxo='rejeitado').count()

    predicoes = PredicaoIA.objects.all()
    altas = predicoes.filter(faixa_risco='alto').count()
    medias = predicoes.filter(faixa_risco='medio').count()
    baixas = predicoes.filter(faixa_risco='baixo').count()

    validacoes = ValidacaoEspecialista.objects.select_related('predicao_ia').all()
    concordantes = 0
    for v in validacoes:
        if v.predicao_ia and v.predicao_ia.predicoes_top_k:
            top1 = v.predicao_ia.predicoes_top_k[0].get('nome_cientifico', '').strip().lower()
            if top1 and v.especie_final.strip().lower() == top1:
                concordantes += 1

    duracoes = []
    for item in HistoricoValidacao.objects.filter(evento='validacao_humana').select_related('ponto'):
        if item.ponto and item.ponto.criado_em:
            duracoes.append((item.criado_em - item.ponto.criado_em).total_seconds())
    tempo_medio_validacao_horas = round((sum(duracoes) / len(duracoes)) / 3600, 2) if duracoes else 0

    distribuicao_geografica = list(pontos.values('estado').annotate(total=Count('id')).order_by('-total')[:10])
    top_especies = list(pontos.values('nome_cientifico_sugerido').annotate(total=Count('id')).order_by('-total')[:10])

    territorial = []
    for ponto in pontos[:50]:
        densidade = ponto.validacoes_especialistas.count()
        res = calcular_score_prioridade(ponto, densidade_validacoes=densidade)
        territorial.append({'ponto_id': ponto.id, 'score': res.score, 'componentes': res.componentes})

    data = {
        'total_pontos_submetidos': total,
        'total_pontos_com_imagem': pontos.exclude(foto='').exclude(foto__isnull=True).count(),
        'total_inferencias_realizadas': predicoes.count(),
        'taxa_validacao': round((validados / total), 4) if total else 0,
        'taxa_rejeicao': round((rejeitados / total), 4) if total else 0,
        'concordancia_ia_especialista': round((concordantes / validacoes.count()), 4) if validacoes.exists() else 0,
        'divergencia_ia_especialista': round(1 - (concordantes / validacoes.count()), 4) if validacoes.exists() else 0,
        'tempo_medio_ate_validacao_horas': tempo_medio_validacao_horas,
        'distribuicao_geografica': distribuicao_geografica,
        'top_especies': top_especies,
        'taxa_necessita_revisao': round((pontos.filter(status_fluxo='necessita_revisao').count() / total), 4) if total else 0,
        'confianca_distribuicao': {'alta': altas, 'media': medias, 'baixa': baixas},
        'priorizacao_territorial_amostra': territorial,
    }
    return Response(data)
