# mapping/serializers.py

import logging

from rest_framework import serializers
from .models import (
    PontoPANC, AlertaClimatico, EventoMonitorado, Notificacao, DispositivoPush, CompartilhamentoSocial,
    Conversa, Mensagem, RecomendacaoPANC, IntegracaoEcommerce, ProdutoSemente,
    RoteiroPANC, RoteiroPANCItem, ReferenciaAR, LojaExterno, ProdutoExterno,
    Rota, RotaPonto, PreferenciasUsuario, PlantaReferencial,
    PlantaCustomizada, ModeloAR, HistoricoIdentificacao, PredicaoIA,
    ValidacaoEspecialista, HistoricoValidacao, HistoricoEnriquecimento,
    EnriquecimentoTaxonomicoHistorico,
)
from django.contrib.auth.models import User
from django.utils import timezone

logger = logging.getLogger(__name__)

class AlertaClimaticoSerializer(serializers.ModelSerializer):
    class Meta:
        model = AlertaClimatico
        fields = [
            'tipo', 'descricao', 'severidade', 'inicio', 'fim', 'fonte',
            'municipio', 'uf', 'id_alerta', 'icone'
        ]

class PontoPANCSerializer(serializers.ModelSerializer):
    alertas = serializers.SerializerMethodField()
    nome_popular = serializers.SerializerMethodField()
    nome_cientifico = serializers.SerializerMethodField()
    tipo_local_publico = serializers.SerializerMethodField()
    grupo = serializers.SerializerMethodField()
    foto_url = serializers.SerializerMethodField()
    localizacao = serializers.SerializerMethodField()
    pode_editar = serializers.SerializerMethodField()
    parte_comestivel = serializers.SerializerMethodField()
    comestivel = serializers.SerializerMethodField()
    epoca_frutificacao = serializers.SerializerMethodField()
    epoca_colheita = serializers.SerializerMethodField()
    sazonalidade = serializers.SerializerMethodField()
    enriquecimento = serializers.SerializerMethodField()
    planta_id = serializers.IntegerField(source='planta.id', read_only=True)
    is_fully_enriched = serializers.SerializerMethodField()

    class Meta:
        model = PontoPANC
        fields = [
            'id', 'nome_popular', 'nome_cientifico', 'tipo_local', 'tipo_local_publico', 'colaborador',
            'grupo', 'relato', 'foto_url', 'cidade', 'estado',
            'status_validacao', 'status_enriquecimento',
            'score_identificacao', 'localizacao', 'pode_editar', 'alertas',
            'parte_comestivel', 'comestivel', 'epoca_frutificacao', 'epoca_colheita', 'sazonalidade',
            'comestibilidade_status', 'comestibilidade_confirmada',
            'parte_comestivel_lista', 'parte_comestivel_confirmada',
            'frutificacao_meses', 'frutificacao_confirmada',
            'colheita_periodo', 'colheita_confirmada',
            'fontes_campos_enriquecimento', 'integracoes_utilizadas', 'integracoes_com_falha',
            'enriquecimento_atualizado_em',
            'is_fully_enriched',
            'planta_id',
            'enriquecimento',
        ]

    def get_alertas(self, obj):
        now = timezone.now()
        alertas_climaticos = getattr(obj, "alertas_ordenados", None)
        if alertas_climaticos is None:
            alertas_climaticos = obj.alertas.filter(inicio__lte=now, fim__gte=now).order_by("-inicio")[:3]
        else:
            alertas_climaticos = [a for a in alertas_climaticos if a.inicio <= now <= a.fim][:3]

        eventos_ambientais = getattr(obj, "eventos_monitorados_ordenados", None)
        if eventos_ambientais is None:
            eventos_ambientais = obj.eventos_monitorados.order_by("-ocorrido_em")[:3]
        else:
            eventos_ambientais = eventos_ambientais[:3]

        saida = AlertaClimaticoSerializer(alertas_climaticos, many=True).data
        for evento in eventos_ambientais:
            saida.append(
                {
                    "tipo": evento.get_tipo_evento_display(),
                    "descricao": evento.descricao,
                    "severidade": evento.severidade,
                    "inicio": evento.ocorrido_em,
                    "fim": evento.publicado_em or evento.ocorrido_em,
                    "fonte": evento.fonte,
                    "municipio": obj.cidade,
                    "uf": obj.estado,
                    "id_alerta": evento.external_id or evento.hash_evento,
                    "icone": None,
                    "distancia_metros": evento.distancia_metros,
                    "confianca": evento.confianca,
                    "brilho": evento.brilho,
                    "frp": evento.frp,
                    "tipo_evento": evento.tipo_evento,
                }
            )

        dedup = []
        seen = set()
        for item in saida:
            key = (item.get("fonte"), item.get("id_alerta"), item.get("tipo"), str(item.get("inicio")), str(item.get("fim")))
            if key in seen:
                continue
            seen.add(key)
            dedup.append(item)

        dedup.sort(key=lambda item: item.get("inicio") or "", reverse=True)
        return dedup[:6]

    def get_nome_popular(self, obj):
        if obj.planta and obj.planta.nome_popular:
            return obj.planta.nome_popular
        return obj.nome_popular or obj.nome_popular_sugerido or ''

    def get_nome_cientifico(self, obj):
        if obj.planta and obj.planta.nome_cientifico:
            return obj.planta.nome_cientifico
        return obj.nome_cientifico_sugerido or ''

    def get_tipo_local_publico(self, obj):
        tipo = (obj.tipo_local or "").strip().lower()
        if tipo in {"", "outro"}:
            return None
        return obj.get_tipo_local_display()

    def get_grupo(self, obj):
        return obj.grupo.nome if obj.grupo else None

    def get_foto_url(self, obj):
        if not obj.foto:
            return None
        request = self.context.get('request')
        return request.build_absolute_uri(obj.foto.url) if request else obj.foto.url

    def get_localizacao(self, obj):
        if obj.localizacao:
            return {'type': 'Point', 'coordinates': [obj.localizacao.x, obj.localizacao.y]}
        if obj.longitude is not None and obj.latitude is not None:
            return {'type': 'Point', 'coordinates': [obj.longitude, obj.latitude]}
        return None

    def get_pode_editar(self, obj):
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        if not user or not user.is_authenticated:
            return False
        return user.is_superuser or obj.criado_por_id == user.id or obj.colaborador == user.username

    def get_parte_comestivel(self, obj):
        if getattr(obj, "parte_comestivel_confirmada", False) and obj.parte_comestivel_lista:
            return ", ".join(obj.parte_comestivel_lista)
        if obj.planta and obj.planta.parte_comestivel:
            val = obj.planta.parte_comestivel.strip()
            if val.lower() not in {"não informado", "nao informado", ""}:
                return val
        return None

    def get_comestivel(self, obj):
        # Priorizar dados do enriquecimento do ponto
        if getattr(obj, "comestibilidade_confirmada", False):
            return True if obj.comestibilidade_status == "sim" else (False if obj.comestibilidade_status == "nao" else None)
        if obj.planta and getattr(obj.planta, "comestivel", None) is not None:
            return bool(obj.planta.comestivel)
        return None

    def get_epoca_frutificacao(self, obj):
        if getattr(obj, "frutificacao_confirmada", False) and obj.frutificacao_meses:
            return ", ".join(obj.frutificacao_meses)
        if obj.planta:
            value = getattr(obj.planta, 'epoca_frutificacao', '') or getattr(obj.planta, 'frutificacao', '')
            if value and value.strip().lower() not in {"não informado", "nao informado", "nao_informado", ""}:
                return value.strip()
        return None

    def get_epoca_colheita(self, obj):
        if getattr(obj, "colheita_confirmada", False) and obj.colheita_periodo:
            if isinstance(obj.colheita_periodo, list):
                return ", ".join(obj.colheita_periodo)
            return str(obj.colheita_periodo).strip() if str(obj.colheita_periodo).strip().lower() not in {"nao_informado", "não informado"} else None
        if obj.planta:
            value = getattr(obj.planta, 'epoca_colheita', '') or getattr(obj.planta, 'colheita', '')
            if value and value.strip().lower() not in {"não informado", "nao informado", "nao_informado", ""}:
                return value.strip()
        return None

    def get_sazonalidade(self, obj):
        dados = {}
        frutificacao = self.get_epoca_frutificacao(obj)
        colheita = self.get_epoca_colheita(obj)
        if frutificacao:
            dados["frutificacao"] = frutificacao
        if colheita:
            dados["colheita"] = colheita
        return dados or None

    def get_historico_validacao(self, obj):
        historico = getattr(obj, "historico_enriquecimento", None)
        if hasattr(historico, "all"):
            historico = historico.all()[:5]
        else:
            historico = EnriquecimentoTaxonomicoHistorico.objects.filter(ponto=obj).order_by("-executado_em")[:5]
        return [
            {
                "status": item.status,
                "grau_confianca": item.grau_confianca,
                "fontes": item.fontes,
                "executado_em": item.executado_em,
            }
            for item in historico
        ]

    def get_enriquecimento(self, obj):
        status = obj.status_enriquecimento or 'pendente'
        if status == 'pendente':
            logger.debug("Serialização enriquecimento: ponto=%s sem dados (status pendente).", obj.id)
            return None
        grau = obj.grau_confianca_taxonomica
        if status == 'completo' and grau and grau >= 0.7:
            selo = 'validado'
        elif status in ('parcial', 'completo') and grau and grau >= 0.3:
            selo = 'parcialmente_validado'
        else:
            selo = 'pendente'
        payload = {
            'nome_cientifico_validado': obj.nome_cientifico_validado or '',
            'nome_aceito': obj.nome_aceito or '',
            'autoria': obj.autoria or '',
            'sinonimos': obj.sinonimos or [],
            'fonte_taxonomica_primaria': obj.fonte_taxonomica_primaria or '',
            'fontes_secundarias': obj.fontes_taxonomicas_secundarias or [],
            'grau_confianca': obj.grau_confianca_taxonomica,
            'distribuicao_resumida': obj.distribuicao_resumida or '',
            'ocorrencias_gbif': obj.ocorrencias_gbif,
            'ocorrencias_inaturalist': obj.ocorrencias_inaturalist,
            'fenologia_observada': obj.fenologia_observada or {},
            'imagem_url': obj.imagem_url or '',
            'imagem_fonte': obj.imagem_fonte or '',
            'licenca_imagem': obj.licenca_imagem or '',
            'ultima_validacao_em': obj.ultima_validacao_em.isoformat() if obj.ultima_validacao_em else None,
            'status_enriquecimento': status,
            'selo_validacao': selo,
            'is_fully_enriched': bool(getattr(obj.planta, "is_fully_enriched", False)) if obj.planta_id else False,
            'fonte_leitura': 'base_local' if (obj.planta_id and getattr(obj.planta, "is_fully_enriched", False)) else 'integracoes_externas',
        }
        logger.debug(
            "Serialização enriquecimento: ponto=%s status=%s fontes=%s.",
            obj.id,
            status,
            obj.integracoes_utilizadas or [],
        )
        return payload

    def get_is_fully_enriched(self, obj):
        return bool(obj.planta_id and getattr(obj.planta, "is_fully_enriched", False))


class PredicaoIASerializer(serializers.ModelSerializer):
    class Meta:
        model = PredicaoIA
        fields = [
            'id', 'ponto', 'historico_identificacao', 'provedor', 'predicoes_top_k',
            'score_confianca', 'faixa_risco', 'justificativa',
            'requer_revisao_humana', 'fonte_predicao', 'criado_em'
        ]
        read_only_fields = ['id', 'criado_em']


class ValidacaoEspecialistaSerializer(serializers.ModelSerializer):
    revisor_username = serializers.CharField(source='revisor.username', read_only=True)

    class Meta:
        model = ValidacaoEspecialista
        fields = [
            'id', 'ponto', 'revisor', 'revisor_username', 'predicao_ia', 'decisao_final',
            'especie_final', 'motivo_divergencia', 'observacao', 'criado_em'
        ]
        read_only_fields = ['id', 'criado_em', 'revisor', 'revisor_username']


class HistoricoValidacaoSerializer(serializers.ModelSerializer):
    usuario_username = serializers.CharField(source='usuario.username', read_only=True)

    class Meta:
        model = HistoricoValidacao
        fields = ['id', 'ponto', 'usuario', 'usuario_username', 'evento', 'dados', 'criado_em']
        read_only_fields = ['id', 'criado_em', 'usuario_username']


# ===================================
# SERIALIZERS - NOTIFICAÇÕES
# ===================================
class DispositivoPushSerializer(serializers.ModelSerializer):
    class Meta:
        model = DispositivoPush
        fields = ['id', 'token', 'plataforma', 'ativo', 'criado_em']
        read_only_fields = ['id', 'criado_em']


class NotificacaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notificacao
        fields = [
            'id', 'tipo', 'titulo', 'mensagem', 'lida',
            'enviada_push', 'link', 'dados_extra', 'criada_em', 'lida_em'
        ]
        read_only_fields = ['id', 'criada_em', 'lida_em']


# ===================================
# SERIALIZERS - MENSAGENS
# ===================================
class UsuarioSimplificadoSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name']


class MensagemSerializer(serializers.ModelSerializer):
    remetente = UsuarioSimplificadoSerializer(read_only=True)

    class Meta:
        model = Mensagem
        fields = [
            'id', 'conversa', 'remetente', 'conteudo',
            'lida', 'imagem', 'enviada_em', 'lida_em'
        ]
        read_only_fields = ['id', 'enviada_em', 'lida_em']


class ConversaSerializer(serializers.ModelSerializer):
    participantes = UsuarioSimplificadoSerializer(many=True, read_only=True)
    ultima_mensagem = serializers.SerializerMethodField()
    mensagens_nao_lidas = serializers.SerializerMethodField()

    class Meta:
        model = Conversa
        fields = [
            'id', 'participantes', 'ultima_mensagem',
            'mensagens_nao_lidas', 'criada_em', 'atualizada_em'
        ]
        read_only_fields = ['id', 'criada_em', 'atualizada_em']

    def get_ultima_mensagem(self, obj):
        ultima = obj.mensagens.order_by('-enviada_em').first()
        if ultima:
            return MensagemSerializer(ultima).data
        return None

    def get_mensagens_nao_lidas(self, obj):
        usuario = self.context.get('request').user
        return obj.mensagens.filter(lida=False).exclude(remetente=usuario).count()


# ===================================
# SERIALIZERS - COMPARTILHAMENTO SOCIAL
# ===================================
class CompartilhamentoSocialSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompartilhamentoSocial
        fields = [
            'id', 'ponto', 'usuario', 'canal',
            'url_compartilhada', 'criado_em'
        ]
        read_only_fields = ['id', 'criado_em']


# ===================================
# SERIALIZERS - RECOMENDAÇÕES
# ===================================
class PlantaReferencialSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlantaReferencial
        fields = [
            'id', 'nome_popular', 'nome_cientifico', 'parte_comestivel',
            'forma_uso', 'grupo_taxonomico', 'origem', 'bioma'
        ]


class RecomendacaoPANCSerializer(serializers.ModelSerializer):
    planta = PlantaReferencialSerializer(read_only=True)

    class Meta:
        model = RecomendacaoPANC
        fields = [
            'id', 'planta', 'score', 'razao',
            'visualizada', 'criada_em'
        ]
        read_only_fields = ['id', 'criada_em']


# ===================================
# SERIALIZERS - E-COMMERCE
# ===================================
class IntegracaoEcommerceSerializer(serializers.ModelSerializer):
    class Meta:
        model = IntegracaoEcommerce
        fields = ['id', 'nome', 'base_url', 'ativo', 'ultima_sincronizacao']
        read_only_fields = ['id', 'ultima_sincronizacao']


class ProdutoSementeSerializer(serializers.ModelSerializer):
    integracao = IntegracaoEcommerceSerializer(read_only=True)
    integracao_id = serializers.PrimaryKeyRelatedField(
        source='integracao',
        queryset=IntegracaoEcommerce.objects.all(),
        write_only=True
    )
    planta = PlantaReferencialSerializer(read_only=True)
    planta_id = serializers.PrimaryKeyRelatedField(
        source='planta',
        queryset=PlantaReferencial.objects.all(),
        write_only=True,
        allow_null=True,
        required=False
    )

    class Meta:
        model = ProdutoSemente
        fields = [
            'id', 'nome', 'url', 'preco', 'disponivel',
            'integracao', 'integracao_id', 'planta', 'planta_id'
        ]
        read_only_fields = ['id']


class LojaExternoSerializer(serializers.ModelSerializer):
    class Meta:
        model = LojaExterno
        fields = ['id', 'nome', 'descricao', 'url', 'logo', 'ativo']


class ProdutoExternoSerializer(serializers.ModelSerializer):
    loja = LojaExternoSerializer(read_only=True)
    planta = PlantaReferencialSerializer(read_only=True)

    class Meta:
        model = ProdutoExterno
        fields = [
            'id', 'loja', 'planta', 'nome', 'descricao',
            'preco', 'url_produto', 'imagem', 'disponivel'
        ]


# ===================================
# SERIALIZERS - ROTAS
# ===================================
class RoteiroPANCItemSerializer(serializers.ModelSerializer):
    ponto = PontoPANCSerializer(read_only=True)
    ponto_id = serializers.PrimaryKeyRelatedField(
        source='ponto',
        queryset=PontoPANC.objects.all(),
        write_only=True
    )

    class Meta:
        model = RoteiroPANCItem
        fields = ['id', 'roteiro', 'ponto', 'ponto_id', 'ordem', 'observacao']
        read_only_fields = ['id']


class RoteiroPANCSerializer(serializers.ModelSerializer):
    criador = UsuarioSimplificadoSerializer(read_only=True)
    itens = RoteiroPANCItemSerializer(many=True, read_only=True)

    class Meta:
        model = RoteiroPANC
        fields = ['id', 'titulo', 'descricao', 'criador', 'criado_em', 'itens']
        read_only_fields = ['id', 'criado_em']


class ReferenciaARSerializer(serializers.ModelSerializer):
    planta = PlantaReferencialSerializer(read_only=True)
    planta_id = serializers.PrimaryKeyRelatedField(
        source='planta',
        queryset=PlantaReferencial.objects.all(),
        write_only=True,
        allow_null=True,
        required=False
    )

    class Meta:
        model = ReferenciaAR
        fields = ['id', 'titulo', 'descricao', 'asset_url', 'criado_em', 'planta', 'planta_id']
        read_only_fields = ['id', 'criado_em']


class RotaPontoSerializer(serializers.ModelSerializer):
    ponto = PontoPANCSerializer(read_only=True)

    class Meta:
        model = RotaPonto
        fields = [
            'id', 'ponto', 'ordem', 'visitado',
            'data_visita', 'notas'
        ]


class RotaSerializer(serializers.ModelSerializer):
    pontos_detalhados = serializers.SerializerMethodField()
    usuario = UsuarioSimplificadoSerializer(read_only=True)

    class Meta:
        model = Rota
        fields = [
            'id', 'usuario', 'nome', 'descricao', 'pontos_detalhados',
            'publica', 'distancia_total', 'tempo_estimado',
            'criada_em', 'atualizada_em'
        ]
        read_only_fields = ['id', 'criada_em', 'atualizada_em']

    def get_pontos_detalhados(self, obj):
        pontos = RotaPonto.objects.filter(rota=obj).order_by('ordem')
        return RotaPontoSerializer(pontos, many=True).data


# ===================================
# SERIALIZERS - PREFERÊNCIAS
# ===================================
class PreferenciasUsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = PreferenciasUsuario
        fields = [
            'notif_novo_ponto', 'notif_validacao', 'notif_mensagens',
            'notif_alertas', 'notif_push', 'idioma', 'perfil_publico',
            'mostrar_localizacao', 'permitir_mensagens'
        ]


# ===================================
# SERIALIZERS - PLANTAS CUSTOMIZADAS & AR
# ===================================
class PlantaCustomizadaSerializer(serializers.ModelSerializer):
    planta_base = PlantaReferencialSerializer(read_only=True)
    planta_base_id = serializers.IntegerField(write_only=True)
    cadastrado_por = UsuarioSimplificadoSerializer(read_only=True)
    especialista_validador = UsuarioSimplificadoSerializer(read_only=True)

    class Meta:
        model = PlantaCustomizada
        fields = [
            'id', 'planta_base', 'planta_base_id', 'nome_variacao', 'descricao',
            'cor_folha', 'formato_folha', 'tamanho_medio', 'textura',
            'cor_flor', 'epoca_floracao', 'caracteristicas_especiais',
            'foto_folha', 'foto_flor', 'foto_fruto', 'foto_planta_inteira',
            'features_ml', 'regiao_encontrada', 'clima_predominante',
            'cadastrado_por', 'validado_por_especialista', 'especialista_validador',
            'criado_em', 'atualizado_em'
        ]
        read_only_fields = ['id', 'criado_em', 'atualizado_em', 'features_ml']


class ModeloARSerializer(serializers.ModelSerializer):
    planta = PlantaReferencialSerializer(read_only=True)
    planta_id = serializers.IntegerField(write_only=True)
    criado_por = UsuarioSimplificadoSerializer(read_only=True)
    modelo_url = serializers.SerializerMethodField()
    preview_url = serializers.SerializerMethodField()

    class Meta:
        model = ModeloAR
        fields = [
            'id', 'planta', 'planta_id', 'nome', 'descricao',
            'modelo_glb', 'modelo_url', 'preview_image', 'preview_url',
            'escala_padrao', 'rotacao_inicial', 'posicao_inicial',
            'animacoes_disponiveis', 'permite_interacao',
            'tamanho_arquivo', 'formato', 'ativo',
            'criado_por', 'criado_em', 'atualizado_em'
        ]
        read_only_fields = ['id', 'criado_em', 'atualizado_em', 'tamanho_arquivo']

    def get_modelo_url(self, obj):
        if obj.modelo_glb:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.modelo_glb.url)
            return obj.modelo_glb.url
        return None

    def get_preview_url(self, obj):
        if obj.preview_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.preview_image.url)
            return obj.preview_image.url
        return None


class HistoricoIdentificacaoSerializer(serializers.ModelSerializer):
    planta_identificada = PlantaReferencialSerializer(read_only=True)
    planta_customizada_identificada = PlantaCustomizadaSerializer(read_only=True)
    usuario = UsuarioSimplificadoSerializer(read_only=True)

    class Meta:
        model = HistoricoIdentificacao
        fields = [
            'id', 'ponto', 'usuario', 'metodo', 'imagem',
            'planta_identificada', 'planta_customizada_identificada',
            'score_confianca', 'resultados_completos',
            'sucesso', 'erro', 'tempo_processamento', 'criado_em'
        ]
        read_only_fields = ['id', 'criado_em']


class IdentificacaoRequestSerializer(serializers.Serializer):
    """
    Serializer para request de identificação de planta
    """
    imagem = serializers.ImageField(required=True)
    usar_custom_db = serializers.BooleanField(default=True)
    usar_google = serializers.BooleanField(default=True)
    salvar_historico = serializers.BooleanField(default=True)


class IdentificacaoResponseSerializer(serializers.Serializer):
    """
    Serializer para response de identificação de planta
    """
    sucesso = serializers.BooleanField()
    metodo = serializers.CharField()
    nome_popular = serializers.CharField(allow_blank=True)
    nome_cientifico = serializers.CharField(allow_blank=True)
    score = serializers.FloatField()
    planta_base_id = serializers.IntegerField(required=False, allow_null=True)
    planta_customizada_id = serializers.IntegerField(required=False, allow_null=True)
    descricao = serializers.CharField(required=False, allow_blank=True)
    tempo_processamento = serializers.FloatField()
    erro = serializers.CharField(required=False, allow_blank=True)


# ===================================
# SERIALIZERS - ENRIQUECIMENTO TAXONÔMICO
# ===================================
class EnriquecimentoPlantaSerializer(serializers.ModelSerializer):
    """Serializer com campos de enriquecimento da PlantaReferencial."""
    selo_validacao = serializers.SerializerMethodField()

    class Meta:
        model = PlantaReferencial
        fields = [
            'id', 'nome_popular', 'nome_cientifico',
            'nome_cientifico_submetido', 'nome_cientifico_validado',
            'nome_aceito', 'sinonimos', 'autoria',
            'fonte_taxonomica_primaria', 'fontes_secundarias',
            'grau_confianca', 'distribuicao_resumida',
            'ocorrencias_gbif', 'ocorrencias_inaturalist',
            'fenologia_observada', 'imagem_url', 'imagem_fonte',
            'licenca_imagem', 'ultima_validacao_em',
            'status_enriquecimento', 'selo_validacao',
        ]
        read_only_fields = fields

    def get_selo_validacao(self, obj):
        status = obj.status_enriquecimento or 'pendente'
        grau = obj.grau_confianca
        if status == 'completo' and grau and grau >= 0.7:
            return 'validado'
        elif status in ('parcial', 'completo') and grau and grau >= 0.3:
            return 'parcialmente_validado'
        return 'pendente'


class HistoricoEnriquecimentoSerializer(serializers.ModelSerializer):
    usuario_username = serializers.CharField(source='usuario.username', read_only=True, default='')

    class Meta:
        model = HistoricoEnriquecimento
        fields = [
            'id', 'planta', 'data', 'fontes_consultadas',
            'resultado', 'status', 'erro_detalhes', 'usuario_username',
        ]
        read_only_fields = fields


class EnriquecimentoRequestSerializer(serializers.Serializer):
    nome_cientifico = serializers.CharField(required=True, max_length=300)
    planta_id = serializers.IntegerField(required=False, allow_null=True)


class EnriquecimentoResponseSerializer(serializers.Serializer):
    sucesso = serializers.BooleanField()
    status = serializers.CharField()
    nome_cientifico_submetido = serializers.CharField(allow_blank=True)
    nome_cientifico_validado = serializers.CharField(allow_blank=True)
    nome_aceito = serializers.CharField(allow_blank=True)
    sinonimos = serializers.ListField(child=serializers.CharField())
    autoria = serializers.CharField(allow_blank=True)
    fonte_taxonomica_primaria = serializers.CharField(allow_blank=True)
    fontes_secundarias = serializers.ListField(child=serializers.CharField())
    grau_confianca = serializers.FloatField(allow_null=True)
    distribuicao_resumida = serializers.CharField(allow_blank=True)
    ocorrencias_gbif = serializers.IntegerField(allow_null=True)
    ocorrencias_inaturalist = serializers.IntegerField(allow_null=True)
    fenologia_observada = serializers.DictField()
    imagem_url = serializers.CharField(allow_blank=True)
    imagem_fonte = serializers.CharField(allow_blank=True)
    licenca_imagem = serializers.CharField(allow_blank=True)
    erros = serializers.ListField(child=serializers.CharField())
    fontes_consultadas = serializers.ListField(child=serializers.CharField())
    payload_resumido = serializers.DictField(required=False, default=dict)
    trefle_extras = serializers.DictField(required=False, allow_null=True, default=None)
