"""
Views para funcionalidades de AR e Identificação Avançada de Plantas
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.shortcuts import get_object_or_404
from django.db.models import Q

from .models import (
    PlantaCustomizada,
    ModeloAR,
    HistoricoIdentificacao,
    PlantaReferencial,
    PontoPANC
)
from .serializers import (
    PlantaCustomizadaSerializer,
    ModeloARSerializer,
    HistoricoIdentificacaoSerializer,
    IdentificacaoRequestSerializer,
    IdentificacaoResponseSerializer
)
from .identificacao_avancada import IdentificadorPlantas
from .services.mobile_parity_service import MobileParityService

mobile_parity_service = MobileParityService()


# ===================================
# VIEWSET - PLANTAS CUSTOMIZADAS
# ===================================
class PlantaCustomizadaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciar plantas customizadas (variações específicas)
    """
    queryset = PlantaCustomizada.objects.all()
    serializer_class = PlantaCustomizadaSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        queryset = PlantaCustomizada.objects.all()

        # Filtrar apenas validadas por padrão
        apenas_validadas = self.request.query_params.get('validadas', 'true')
        if apenas_validadas.lower() == 'true':
            queryset = queryset.filter(validado_por_especialista=True)

        # Filtrar por planta base
        planta_base_id = self.request.query_params.get('planta_base')
        if planta_base_id:
            queryset = queryset.filter(planta_base_id=planta_base_id)

        # Filtrar por região
        regiao = self.request.query_params.get('regiao')
        if regiao:
            queryset = queryset.filter(regiao_encontrada__icontains=regiao)

        return queryset.order_by('-criado_em')

    def perform_create(self, serializer):
        # Salvar com o usuário atual como cadastrador
        serializer.save(cadastrado_por=self.request.user)

    @action(detail=True, methods=['post'])
    def validar(self, request, pk=None):
        """
        Endpoint para especialista validar uma planta customizada
        """
        planta = self.get_object()

        # Verificar se usuário é especialista (implementar lógica conforme necessário)
        # Por exemplo, verificar se está no grupo de especialistas
        if not request.user.groups.filter(name='Especialistas').exists():
            return Response(
                {'erro': 'Apenas especialistas podem validar plantas'},
                status=status.HTTP_403_FORBIDDEN
            )

        planta.validado_por_especialista = True
        planta.especialista_validador = request.user
        planta.save()

        return Response({
            'mensagem': 'Planta validada com sucesso',
            'planta': PlantaCustomizadaSerializer(planta, context={'request': request}).data
        })

    @action(detail=True, methods=['post'])
    def extrair_features(self, request, pk=None):
        """
        Extrai features ML de uma foto específica da planta customizada
        """
        planta = self.get_object()

        # Verificar qual foto usar
        tipo_foto = request.data.get('tipo_foto', 'planta_inteira')

        foto_map = {
            'folha': planta.foto_folha,
            'flor': planta.foto_flor,
            'fruto': planta.foto_fruto,
            'planta_inteira': planta.foto_planta_inteira
        }

        foto = foto_map.get(tipo_foto)
        if not foto:
            return Response(
                {'erro': f'Foto do tipo {tipo_foto} não encontrada'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Extrair features
        try:
            identificador = IdentificadorPlantas()
            features = identificador._extrair_features_imagem(foto.path)

            # Salvar features
            planta.features_ml = features
            planta.save()

            return Response({
                'mensagem': 'Features extraídas com sucesso',
                'features': features
            })
        except Exception as e:
            return Response(
                {'erro': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ===================================
# VIEWSET - MODELOS AR
# ===================================
class ModeloARViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciar modelos 3D de Realidade Aumentada
    """
    queryset = ModeloAR.objects.filter(ativo=True)
    serializer_class = ModeloARSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        queryset = ModeloAR.objects.filter(ativo=True)

        # Filtrar por planta
        planta_id = self.request.query_params.get('planta')
        if planta_id:
            queryset = queryset.filter(planta_id=planta_id)

        # Filtrar por formato
        formato = self.request.query_params.get('formato')
        if formato:
            queryset = queryset.filter(formato=formato)

        return queryset.order_by('-criado_em')

    def perform_create(self, serializer):
        # Calcular tamanho do arquivo
        modelo_file = self.request.FILES.get('modelo_glb')
        tamanho = modelo_file.size if modelo_file else None

        serializer.save(
            criado_por=self.request.user,
            tamanho_arquivo=tamanho
        )

    @action(detail=True, methods=['get'])
    def preview(self, request, pk=None):
        """
        Retorna preview do modelo AR
        """
        modelo = self.get_object()
        return Response({
            'id': modelo.id,
            'nome': modelo.nome,
            'planta': modelo.planta.nome_popular,
            'preview_url': request.build_absolute_uri(modelo.preview_image.url) if modelo.preview_image else None,
            'escala_padrao': modelo.escala_padrao,
            'permite_interacao': modelo.permite_interacao
        })


# ===================================
# VIEWSET - HISTÓRICO IDENTIFICAÇÃO
# ===================================
class HistoricoIdentificacaoViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet somente leitura para histórico de identificações
    """
    queryset = HistoricoIdentificacao.objects.all()
    serializer_class = HistoricoIdentificacaoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = HistoricoIdentificacao.objects.all()

        # Filtrar por usuário
        if not self.request.user.is_staff:
            queryset = queryset.filter(usuario=self.request.user)

        # Filtrar por método
        metodo = self.request.query_params.get('metodo')
        if metodo:
            queryset = queryset.filter(metodo=metodo)

        # Filtrar apenas sucessos
        apenas_sucesso = self.request.query_params.get('sucesso')
        if apenas_sucesso:
            queryset = queryset.filter(sucesso=True)

        return queryset.order_by('-criado_em')

    @action(detail=False, methods=['get'])
    def estatisticas(self, request):
        """
        Retorna estatísticas de identificação do usuário
        """
        historico = self.get_queryset()

        total = historico.count()
        sucesso = historico.filter(sucesso=True).count()
        por_metodo = {}

        for metodo, _ in HistoricoIdentificacao.METODO_CHOICES:
            por_metodo[metodo] = historico.filter(metodo=metodo).count()

        return Response({
            'total_identificacoes': total,
            'taxa_sucesso': (sucesso / total * 100) if total > 0 else 0,
            'por_metodo': por_metodo,
            'tempo_medio': historico.filter(
                tempo_processamento__isnull=False
            ).aggregate(
                media=models.Avg('tempo_processamento')
            )['media'] or 0
        })


# ===================================
# API - IDENTIFICAÇÃO DE PLANTAS
# ===================================
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def identificar_planta_view(request):
    """
    Endpoint principal para identificação de plantas

    POST /api/identificar-planta/
    Body (multipart/form-data):
        - imagem: arquivo de imagem
        - usar_custom_db: boolean (default: true)
        - usar_google: boolean (default: true)
        - salvar_historico: boolean (default: true)
        - ponto_id: int (opcional, vincular a um ponto)
    """
    serializer = IdentificacaoRequestSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # Obter parâmetros
    imagem = request.FILES.get('imagem')
    usar_custom_db = serializer.validated_data.get('usar_custom_db', True)
    usar_google = serializer.validated_data.get('usar_google', True)
    salvar_historico = serializer.validated_data.get('salvar_historico', True)
    ponto_id = request.data.get('ponto_id')

    try:
        resultado_normalizado = mobile_parity_service.identificar_por_imagem(
            imagem,
            usar_custom_db=usar_custom_db,
            usar_google=usar_google,
        )
        resultado = resultado_normalizado.payload

        # Salvar histórico se solicitado
        if salvar_historico:
            ponto = None
            if ponto_id:
                ponto = get_object_or_404(PontoPANC, id=ponto_id)

            # Buscar plantas identificadas
            planta_base = None
            planta_customizada = None

            if resultado.get('planta_base_id'):
                planta_base = PlantaReferencial.objects.filter(
                    id=resultado['planta_base_id']
                ).first()

            if resultado.get('planta_customizada_id'):
                planta_customizada = PlantaCustomizada.objects.filter(
                    id=resultado['planta_customizada_id']
                ).first()

            # Criar histórico
            historico = HistoricoIdentificacao.objects.create(
                ponto=ponto,
                usuario=request.user,
                metodo=resultado.get('metodo', 'nenhum'),
                imagem=imagem,
                planta_identificada=planta_base,
                planta_customizada_identificada=planta_customizada,
                score_confianca=resultado.get('score', 0.0) * 100,
                resultados_completos=resultado,
                sucesso=resultado.get('score', 0) > 0.5,
                erro=resultado.get('erro', ''),
                tempo_processamento=resultado.get('tempo_processamento', 0)
            )

            resultado['historico_id'] = historico.id

        return Response(resultado, status=status.HTTP_200_OK)

    except Exception as e:
        return Response(
            {'erro': f'Erro ao identificar planta: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def buscar_plantas_view(request):
    """
    Busca plantas por nome (popular ou científico)

    GET /api/buscar-plantas/?q=termo
    """
    termo = request.query_params.get('q', '')

    if not termo or len(termo) < 2:
        return Response(
            {'erro': 'Termo de busca deve ter pelo menos 2 caracteres'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Buscar em plantas referenciais
    plantas_ref = PlantaReferencial.objects.filter(
        Q(nome_popular__icontains=termo) |
        Q(nome_cientifico__icontains=termo) |
        Q(nome_cientifico_valido__icontains=termo)
    )[:10]

    # Buscar em plantas customizadas validadas
    plantas_custom = PlantaCustomizada.objects.filter(
        validado_por_especialista=True
    ).filter(
        Q(nome_variacao__icontains=termo) |
        Q(planta_base__nome_popular__icontains=termo) |
        Q(planta_base__nome_cientifico__icontains=termo)
    )[:5]

    from .serializers import PlantaReferencialSerializer

    return Response({
        'plantas_referenciais': PlantaReferencialSerializer(plantas_ref, many=True).data,
        'plantas_customizadas': PlantaCustomizadaSerializer(
            plantas_custom,
            many=True,
            context={'request': request}
        ).data
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def modelos_ar_disponiveis(request):
    """
    Lista modelos AR disponíveis (público)

    GET /api/modelos-ar-disponiveis/
    """
    planta_id = request.query_params.get('planta')

    modelos = ModeloAR.objects.filter(ativo=True)
    if planta_id:
        modelos = modelos.filter(planta_id=planta_id)

    modelos = modelos.order_by('-criado_em')[:20]

    return Response({
        'modelos': ModeloARSerializer(
            modelos,
            many=True,
            context={'request': request}
        ).data
    })
