from django.contrib import admin
from django.contrib.gis.admin import OSMGeoAdmin
from .models import (
    PlantaReferencial, PontoPANC, ParecerValidacao,
    Badge, Feedback, Missao, HistoricoGamificacao,
    PontuacaoUsuario, SugestaoMissao, BotaoFlutuante,
    MissaoUsuario, RankingRevisor, Nivel, Grupo, UsuarioBadge,
    AlertaClimatico, DispositivoPush, Notificacao, Conversa, Mensagem,
    CompartilhamentoSocial, RecomendacaoPANC, IntegracaoEcommerce,
    ProdutoSemente, RoteiroPANC, RoteiroPANCItem, ReferenciaAR,
    IntegracaoMonitoramento, IntegracaoMonitoramentoLog
)

# =======================
# Plantas referenciais
# =======================
@admin.register(PlantaReferencial)
class PlantaReferencialAdmin(admin.ModelAdmin):
    list_display = (
        'nome_popular', 'nome_cientifico', 'comestivel', 'parte_comestivel', 'epoca_frutificacao', 'epoca_colheita', 'forma_uso',
        'grupo_taxonomico', 'origem', 'bioma', 'regiao_ocorrencia',
        'nome_cientifico_valido', 'nome_cientifico_corrigido', 'fonte_validacao'
    )
    search_fields = (
        'nome_popular', 'nome_cientifico', 'parte_comestivel', 'forma_uso'
    )
    list_filter = (
        'grupo_taxonomico', 'bioma', 'regiao_ocorrencia'
    )
    ordering = ('nome_popular',)

# =======================
# Pontos de PANCs
# =======================
@admin.register(PontoPANC)
class PontoPANCAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'cidade', 'estado', 'status_identificacao', 'status_validacao', 'criado_em')
    list_filter = ('status_identificacao', 'status_validacao', 'tipo_local', 'estado')
    search_fields = ('nome_popular', 'cidade', 'estado', 'colaborador', 'relato')
    readonly_fields = ('criado_em',)
    autocomplete_fields = ['planta']
    fieldsets = (
        (None, {
            'fields': (
                'planta', 'nome_popular', 'tipo_local', 'endereco', 'numero', 'bairro',
                'cidade', 'estado', 'colaborador', 'relato', 'foto', 'localizacao',
            )
        }),
        ('Identificação por IA', {
            'fields': (
                'nome_popular_sugerido', 'nome_cientifico_sugerido',
                'score_identificacao', 'status_identificacao',
            )
        }),
        ('Validação', {
            'fields': ('status_validacao', 'grupo', 'criado_em')
        }),
    )

# =======================
# Alertas Climáticos
# =======================
@admin.register(AlertaClimatico)
class AlertaClimaticoAdmin(admin.ModelAdmin):
    list_display = ('ponto', 'tipo', 'inicio', 'fim', 'criado_em', 'fonte')
    list_filter = ('tipo', 'inicio', 'fim', 'fonte')
    search_fields = ('ponto__nome_popular', 'tipo', 'descricao')
    ordering = ('-inicio',)

# =======================
# Pareceres de validação
# =======================
@admin.register(ParecerValidacao)
class ParecerValidacaoAdmin(admin.ModelAdmin):
    list_display = ('ponto', 'especialista', 'parecer', 'data')
    list_filter = ('parecer', 'data', 'especialista')
    search_fields = ('ponto__id', 'especialista__username', 'comentario')
    ordering = ('-data',)

# =======================
# Grupos / Comunidades
# =======================
@admin.register(Grupo)
class GrupoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'descricao')
    search_fields = ('nome', 'descricao')
    filter_horizontal = ('membros',)
    ordering = ('nome',)

# =======================
# Badges (Gamificação)
# =======================
@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ('nome', 'descricao', 'nivel', 'missao')
    search_fields = ('nome', 'descricao', 'missao__titulo')
    list_filter = ('nivel', 'missao')
    ordering = ('nome',)

# =======================
# Associação Usuário-Badge (Conquistas)
# =======================
@admin.register(UsuarioBadge)
class UsuarioBadgeAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'badge', 'data_conquista')
    search_fields = ('usuario__username', 'badge__nome')
    list_filter = ('badge', 'usuario', 'data_conquista')
    ordering = ('-data_conquista',)

# =======================
# Feedback de usuários
# =======================
@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'ponto', 'mensagem', 'criado_em')
    search_fields = ('usuario__username', 'mensagem', 'ponto__id')
    list_filter = ('criado_em',)
    ordering = ('-criado_em',)

# =======================
# Níveis
# =======================
@admin.register(Nivel)
class NivelAdmin(admin.ModelAdmin):
    list_display = ['numero', 'nome', 'pontos_minimos', 'pontos_maximos', 'beneficios', 'surpresa_oculta']
    list_editable = ['pontos_minimos', 'pontos_maximos', 'beneficios', 'surpresa_oculta']

# =======================
# Pontuação do Usuário
# =======================
@admin.register(PontuacaoUsuario)
class PontuacaoUsuarioAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'pontos', 'nivel', 'atualizado_em')
    search_fields = ('usuario__username',)
    readonly_fields = ('atualizado_em',)

# =======================
# Missões e Gamificação (simples)
# =======================
admin.site.register(Missao)
admin.site.register(HistoricoGamificacao)
admin.site.register(SugestaoMissao)
admin.site.register(BotaoFlutuante)
admin.site.register(MissaoUsuario)
admin.site.register(RankingRevisor)

# =======================
# Notificações e mensagens
# =======================
@admin.register(DispositivoPush)
class DispositivoPushAdmin(admin.ModelAdmin):
    list_display = ("usuario", "plataforma", "ativo", "atualizado_em")
    list_filter = ("plataforma", "ativo")
    search_fields = ("usuario__username", "token")

@admin.register(Notificacao)
class NotificacaoAdmin(admin.ModelAdmin):
    list_display = ("usuario", "titulo", "criada_em", "lida_em")
    list_filter = ("lida_em",)
    search_fields = ("usuario__username", "titulo", "mensagem")

@admin.register(Conversa)
class ConversaAdmin(admin.ModelAdmin):
    list_display = ("id", "criada_em", "atualizada_em")
    filter_horizontal = ("participantes",)

@admin.register(Mensagem)
class MensagemAdmin(admin.ModelAdmin):
    list_display = ("conversa", "remetente", "enviada_em", "lida_em")
    search_fields = ("remetente__username", "conteudo")

@admin.register(CompartilhamentoSocial)
class CompartilhamentoSocialAdmin(admin.ModelAdmin):
    list_display = ("ponto", "usuario", "canal", "criado_em")
    list_filter = ("canal",)
    search_fields = ("ponto__id", "usuario__username", "url_compartilhada")

# =======================
# Roadmap 2.0
# =======================
@admin.register(RecomendacaoPANC)
class RecomendacaoPANCAdmin(admin.ModelAdmin):
    list_display = ("usuario", "planta", "score", "visualizada", "criada_em")
    list_filter = ("visualizada",)
    search_fields = ("usuario__username", "planta__nome_popular")

@admin.register(IntegracaoEcommerce)
class IntegracaoEcommerceAdmin(admin.ModelAdmin):
    list_display = ("nome", "ativo", "ultima_sincronizacao")
    list_filter = ("ativo",)
    search_fields = ("nome", "base_url")

@admin.register(ProdutoSemente)
class ProdutoSementeAdmin(admin.ModelAdmin):
    list_display = ("nome", "integracao", "planta", "preco", "disponivel")
    list_filter = ("integracao", "disponivel")
    search_fields = ("nome", "planta__nome_popular")

@admin.register(RoteiroPANC)
class RoteiroPANCAdmin(admin.ModelAdmin):
    list_display = ("titulo", "criador", "criado_em")
    search_fields = ("titulo", "criador__username")

@admin.register(RoteiroPANCItem)
class RoteiroPANCItemAdmin(admin.ModelAdmin):
    list_display = ("roteiro", "ponto", "ordem")
    list_filter = ("roteiro",)

@admin.register(ReferenciaAR)
class ReferenciaARAdmin(admin.ModelAdmin):
    list_display = ("titulo", "planta", "criado_em")
    search_fields = ("titulo", "planta__nome_popular")


@admin.register(IntegracaoMonitoramento)
class IntegracaoMonitoramentoAdmin(admin.ModelAdmin):
    list_display = ("nome", "status", "ultimo_teste_bem_sucedido", "tempo_resposta_ms", "requer_chave", "atualizado_em")
    list_filter = ("status", "requer_chave")
    search_fields = ("nome", "ultimo_erro", "endpoint_healthcheck")


@admin.register(IntegracaoMonitoramentoLog)
class IntegracaoMonitoramentoLogAdmin(admin.ModelAdmin):
    list_display = ("integracao", "status", "tempo_resposta_ms", "criado_em")
    list_filter = ("status", "integracao")
    search_fields = ("integracao__nome", "detalhe")
