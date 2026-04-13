from django.urls import path, include
from . import views
from .views import (
    historico_alertas, PontoPANCViewSet, mapa_app, api_login, api_register,
    CompartilhamentoSocialViewSet,
    IntegracaoEcommerceViewSet, ProdutoSementeViewSet,
    RoteiroPANCViewSet, RoteiroPANCItemViewSet, ReferenciaARViewSet,
    registrar_push_token, api_notificacoes, api_conversas, api_mensagens,
    api_compartilhamento, api_offline_sync
)
from rest_framework.routers import DefaultRouter
from . import views_api
from . import views_ar_identificacao
from . import views_offline_plantas
from . import views_mapbiomas
from . import views_enrichment
from . import views_climate
from . import views_mobile_parity

router = DefaultRouter()
router.register(r'pontos', PontoPANCViewSet, basename='pontos')
router.register(r'compartilhamentos', CompartilhamentoSocialViewSet, basename='compartilhamentos')
router.register(r'integracoes-ecommerce', IntegracaoEcommerceViewSet, basename='integracoes-ecommerce')
router.register(r'produtos-semente', ProdutoSementeViewSet, basename='produtos-semente')
router.register(r'roteiros', RoteiroPANCViewSet, basename='roteiros')
router.register(r'roteiro-itens', RoteiroPANCItemViewSet, basename='roteiro-itens')
router.register(r'referencias-ar', ReferenciaARViewSet, basename='referencias-ar')

# Registra os novos viewsets da API
router.register(r'notificacoes', views_api.NotificacaoViewSet, basename='notificacoes')
router.register(r'dispositivos-push', views_api.DispositivoPushViewSet, basename='dispositivos-push')
router.register(r'conversas', views_api.ConversaViewSet, basename='conversas')
router.register(r'mensagens', views_api.MensagemViewSet, basename='mensagens')
router.register(r'recomendacoes', views_api.RecomendacaoPANCViewSet, basename='recomendacoes')
router.register(r'lojas', views_api.LojaExternoViewSet, basename='lojas')
router.register(r'produtos', views_api.ProdutoExternoViewSet, basename='produtos')
router.register(r'rotas', views_api.RotaViewSet, basename='rotas')
router.register(r'preferencias', views_api.PreferenciasUsuarioViewSet, basename='preferencias')

# Novos viewsets: AR e Identificação Avançada
router.register(r'plantas-customizadas', views_ar_identificacao.PlantaCustomizadaViewSet, basename='plantas-customizadas')
router.register(r'modelos-ar', views_ar_identificacao.ModeloARViewSet, basename='modelos-ar')
router.register(r'historico-identificacao', views_ar_identificacao.HistoricoIdentificacaoViewSet, basename='historico-identificacao')


urlpatterns = [
    # ---------------- MAPA E CONTRIBUIÇÕES ----------------
    path('', views.mapa, name='mapa'),
    path('cadastro/', views.cadastrar_ponto, name='cadastrar_ponto'),
    path('editar/<int:pk>/', views.editar_ponto, name='editar_ponto'),
    path('remover/<int:pk>/', views.remover_ponto, name='remover_ponto'),
    path('minhas-contribuicoes/', views.painel_contribuicoes, name='painel_contribuicoes'),
    path('ponto/<int:pk>/', views.detalhe_ponto, name='detalhe_ponto'),

    # ---------------- FEEDBACK ----------------
    path('feedback/', views.enviar_feedback, name='feedback'),
    path('feedbacks/', views.lista_feedbacks, name='lista_feedbacks'),

    # ---------------- REVISÃO (Revisor) ----------------
    path('painel-validacao/', views.painel_validacao, name='painel_validacao'),
    path('validar-ponto/<int:ponto_id>/', views.validar_ponto, name='validar_ponto'),

    # ---------------- GRUPOS / COMUNIDADES ----------------
    path('grupos/', views.lista_comunidades, name='lista_comunidades'),
    path('meus-grupos/', views.meus_grupos, name='meus_grupos'),

    # ---------------- GAMIFICAÇÃO: USUÁRIO ----------------
    path('gamificacao/', views.painel_gamificacao, name='painel_gamificacao'),
    path('gamificacao/conquistas/', views.minhas_conquistas, name='minhas_conquistas'),
    path('gamificacao/ranking/', views.ranking_usuarios, name='ranking_usuarios'),
    path('gamificacao/disponiveis/', views.conquistas_disponiveis, name='conquistas_disponiveis'),
    path('gamificacao/historico/', views.historico_gamificacao, name='historico_gamificacao'),
    path('gamificacao/missoes/', views.missoes, name='missoes'),
    path('gamificacao/sugerir-missao/', views.sugerir_missao, name='sugerir_missao'),
    path('gamificacao/remover-botao/', views.remover_botao_flutuante, name='remover_botao_flutuante'),
    path('gamificacao/revisores/', views.ranking_revisores, name='ranking_revisores'),

    # ---------------- GAMIFICAÇÃO: ADMIN ----------------
    path('gamificacao/admin/', views.painel_admin_gamificacao, name='painel_admin_gamificacao'),
    path('gamificacao/criar-missao/', views.criar_missao, name='criar_missao'),
    path('gamificacao/criar-conquista/', views.criar_conquista, name='criar_conquista'),
    path('gamificacao/editar-missao/<int:pk>/', views.editar_missao, name='editar_missao'),
    path('gamificacao/desativar-missao/<int:pk>/', views.desativar_missao, name='desativar_missao'),
    path('gamificacao/excluir-missao/<int:pk>/', views.excluir_missao, name='excluir_missao'),
    path('gamificacao/editar-conquista/<int:pk>/', views.editar_conquista, name='editar_conquista'),
    path('gamificacao/excluir-conquista/<int:pk>/', views.excluir_conquista, name='excluir_conquista'),

    # ---------------- MISSÕES COLABORATIVAS ----------------
    path('gamificacao/criar-missao-usuario/', views.criar_missao_usuario, name='criar_missao_usuario'),
    path('gamificacao/minhas-missoes/', views.minhas_missoes, name='minhas_missoes'),
    path('gamificacao/missoes-colaborativas/', views.missoes_colaborativas, name='missoes_colaborativas'),
    path('gamificacao/missao/<int:missao_id>/ranking/', views.ranking_missao, name='ranking_missao'),
    path('gamificacao/missao/<int:missao_id>/concluir/', views.concluir_missao_usuario, name='concluir_missao_usuario'),
    path('missoes/', views.missoes, name='missoes'),
    # ---------------- API E AJAX ----------------
    path('api/autocomplete-nome/', views.autocomplete_nome_popular, name='autocomplete_nome_popular'),
    path('api/nome-cientifico/', views.buscar_nome_cientifico, name='buscar_nome_cientifico'),
    path('api/identificar/', views.api_identificar, name='api_identificar'),
    path("api/geocode/", views.reverse_geocode, name="reverse_geocode"),
    path("api/offline-sync/", api_offline_sync, name="api_offline_sync"),
    path("api/push-token/", registrar_push_token, name="registrar_push_token"),
    path("api/notificacoes/", api_notificacoes, name="api_notificacoes"),
    path("api/conversas/", api_conversas, name="api_conversas"),
    path("api/mensagens/", api_mensagens, name="api_mensagens"),
    path("api/compartilhamentos/", api_compartilhamento, name="api_compartilhamento"),
    path('api/', include(router.urls)),
    # ---------------- OUTROS ----------------
    path('teste-identificacao/', views.teste_identificacao, name='teste_identificacao'),
    path('obrigado/', views.obrigado, name='obrigado'),

    # ---------------- ADMIN TOOLS ----------------
    path('painel-admin/', views.painel_admin_gamificacao, name='painel_admin_gamificacao'),  # Alias para painel admin de gamificação
    path('painel-admin/integracoes/', views.painel_integracoes, name='painel_integracoes'),
    path('api/admin/integracoes/health/', views.api_health_integracoes, name='api_health_integracoes'),
    path('api/admin/integracoes/testar/', views.api_testar_integracoes, name='api_testar_integracoes'),
    path('exportar_usuarios_csv/', views.exportar_usuarios_csv, name='exportar_usuarios_csv'),
    path('exportar_pontos_csv/', views.exportar_pontos_csv, name='exportar_pontos_csv'),
    # ---------------- Alerta Climatico ----------------
    path('historico-alertas/', historico_alertas, name='historico_alertas'),
    path('alerta/<int:pk>/editar/', views.AlertaUpdateView.as_view(), name='alerta_editar'),
    path('alerta/<int:pk>/excluir/', views.AlertaDeleteView.as_view(), name='alerta_excluir'),
    path('alertas/', views.lista_alertas, name='lista_alertas'),
    path('alerta/novo/', views.alerta_novo, name='alerta_novo'),
    # ---------------- Aplicativo ----------------
    path('mapa/', mapa_app, name='mapa-app'),
    path('api/token/login/', api_login),
    path('api/register/', api_register),
    path('api/user/profile/', views.api_user_profile, name='api_user_profile'),
    path('api/user/change-password/', views.api_change_password, name='api_change_password'),

    # ---------------- NOVAS APIs (v1.1 e v2.0) ----------------
    # Busca avançada
    path('api/busca-avancada/', views_api.busca_avancada_pontos, name='busca_avancada'),

    # Plantas referenciais
    path('api/plantas/', views_api.listar_plantas, name='listar_plantas'),

    # Rotas
    path('api/rotas/sugerir/', views.sugerir_rota_automatica, name='sugerir_rota'),
    path('api/rotas/calcular/', views.calcular_rota, name='calcular_rota'),
    path('api/rotas/pontos-proximos/', views.pontos_proximos, name='pontos_proximos'),

    # Recomendações
    path('api/recomendacoes/atualizar/', views.atualizar_recomendacoes, name='atualizar_recomendacoes'),

    # ---------------- AR E IDENTIFICAÇÃO AVANÇADA ----------------
    # Identificação de plantas com múltiplas fontes (Google Vision, PlantNet, Custom DB)
    path('api/identificar-planta/', views_ar_identificacao.identificar_planta_view, name='identificar_planta'),

    # Busca de plantas
    path('api/buscar-plantas/', views_ar_identificacao.buscar_plantas_view, name='buscar_plantas'),

    # Modelos AR disponíveis (público)
    path('api/modelos-ar-disponiveis/', views_ar_identificacao.modelos_ar_disponiveis, name='modelos_ar_disponiveis'),

    # ---------------- ESPÉCIES REFERENCIAIS (busca canônica) ----------------
    path('api/especies-referenciais/busca/', views_offline_plantas.buscar_especies_referenciais, name='buscar_especies_referenciais'),
    path('api/especies-referenciais/busca-recursiva/', views_offline_plantas.buscar_especies_referenciais_recursiva, name='buscar_especies_referenciais_recursiva'),

    # ---------------- PLANTAS OFFLINE SELETIVAS ----------------
    # Listagem de plantas disponíveis para download
    path('api/plantas-offline/disponiveis/', views_offline_plantas.listar_plantas_disponiveis, name='plantas_offline_disponiveis'),

    # Pacotes pré-definidos
    path('api/plantas-offline/pacotes/', views_offline_plantas.listar_pacotes_offline, name='pacotes_offline'),
    path('api/plantas-offline/pacotes/<int:pacote_id>/baixar/', views_offline_plantas.baixar_pacote, name='baixar_pacote'),

    # Download de plantas selecionadas
    path('api/plantas-offline/baixar/', views_offline_plantas.baixar_plantas_selecionadas, name='baixar_plantas_selecionadas'),
    path('api/plantas-offline/<int:planta_id>/dados/', views_offline_plantas.obter_dados_planta, name='obter_dados_planta'),

    # Gerenciamento de plantas baixadas
    path('api/plantas-offline/minhas/', views_offline_plantas.listar_plantas_baixadas, name='listar_plantas_baixadas'),
    path('api/plantas-offline/<int:planta_id>/remover/', views_offline_plantas.remover_planta_offline, name='remover_planta_offline'),

    # Configurações offline
    path('api/plantas-offline/configuracoes/', views_offline_plantas.configuracoes_offline, name='configuracoes_offline'),

    # Sincronização de status
    path('api/plantas-offline/sincronizar/', views_offline_plantas.sincronizar_status, name='sincronizar_status_offline'),


    # ---------------- NÚCLEO CIENTÍFICO IA ----------------
    path('api/cientifico/pontos/<int:ponto_id>/inferencia/', views_api.InferenciaPontoAPIView.as_view(), name='inferencia_ponto'),
    path('api/cientifico/revisao/fila/', views_api.FilaRevisaoAPIView.as_view(), name='fila_revisao'),
    path('api/cientifico/revisao/pontos/<int:ponto_id>/', views_api.DetalheRevisaoPontoAPIView.as_view(), name='detalhe_revisao_ponto'),
    path('api/cientifico/pontos/<int:ponto_id>/validacao/', views_api.ValidacaoPontoAPIView.as_view(), name='validacao_ponto_cientifico'),
    path('api/cientifico/pontos/<int:ponto_id>/historico/', views_api.HistoricoDecisoesAPIView.as_view(), name='historico_decisoes_ponto'),
    path('api/cientifico/dashboard/', views_api.dashboard_analitico, name='dashboard_analitico'),

    # ---------------- MAPBIOMAS ALERTA ----------------
    # Buscar alertas de desmatamento
    path('api/mapbiomas/alertas/', views_mapbiomas.buscar_alertas_desmatamento, name='mapbiomas_alertas'),

    # Detalhes de um alerta específico
    path('api/mapbiomas/alertas/<str:alert_code>/', views_mapbiomas.buscar_alerta_detalhado, name='mapbiomas_alerta_detalhado'),

    # Buscar territórios (biomas, municípios, UCs)
    path('api/mapbiomas/territorios/', views_mapbiomas.buscar_territorios, name='mapbiomas_territorios'),

    # Alertas por propriedade rural (CAR)
    path('api/mapbiomas/propriedade/', views_mapbiomas.buscar_alertas_propriedade, name='mapbiomas_propriedade'),

    # Informações sobre um ponto específico
    path('api/mapbiomas/ponto/', views_mapbiomas.informacoes_ponto, name='mapbiomas_ponto'),

    # Verificar alertas próximos a um ponto PANC
    path('api/mapbiomas/pontos-panc/<int:ponto_id>/', views_mapbiomas.verificar_alertas_ponto_panc, name='mapbiomas_ponto_panc'),

    # Testar conexão com API
    path('api/mapbiomas/testar/', views_mapbiomas.testar_conexao, name='mapbiomas_testar'),


    # ---------------- CLIMA (pipeline unificado) ----------------
    path('api/alertas-ativos/', views_climate.api_alertas_ativos, name='api_alertas_ativos'),
    path('api/historico_alertas_api/', views_climate.api_historico_alertas, name='api_historico_alertas'),
    path('api/clima/sincronizar/', views_climate.api_sincronizar_alertas_climaticos, name='api_sincronizar_alertas_climaticos'),
    path('api/clima/status/', views_climate.api_status_operacional_clima, name='api_status_operacional_clima'),

    # ---------------- ENRIQUECIMENTO TAXONÔMICO ----------------
    path('api/enriquecimento/', views_enrichment.enriquecer_nome, name='enriquecer_nome'),
    path('api/enriquecimento/revalidar/', views_enrichment.revalidar_planta, name='revalidar_planta'),
    path('api/enriquecimento/<int:planta_id>/', views_enrichment.consultar_enriquecimento, name='consultar_enriquecimento'),
    path('api/enriquecimento/<int:planta_id>/historico/', views_enrichment.historico_enriquecimento, name='historico_enriquecimento'),

    # ---------------- MOBILE PARITY (fonte única web/mobile) ----------------
    path('api/mobile/identificacao/imagem/', views_mobile_parity.identificar_imagem_mobile, name='mobile_identificar_imagem'),
    path('api/mobile/mapa/previews/', views_mobile_parity.mapa_previews_mobile, name='mobile_mapa_previews'),
    path('api/mobile/offline/base/metadata/', views_mobile_parity.offline_base_metadata_mobile, name='mobile_offline_base_metadata'),
    path('api/mobile/offline/base/', views_mobile_parity.offline_base_download_mobile, name='mobile_offline_base_download'),

]
