from django.contrib.gis.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

# =============================
# CHOICES GLOBAIS
# =============================
TIPOS_DE_LOCAL = [
    ('quintal', 'Quintal'),
    ('reserva', 'Reserva'),
    ('rua', 'Beira de rua'),
    ('outro', 'Outro'),
]

STATUS_IDENTIFICACAO = [
    ('confirmado', 'Confirmado'),
    ('sugerido', 'Sugerido pela IA'),
    ('pendente', 'Aguardando revisão'),
]

STATUS_VALIDACAO = [
    ('pendente', 'Em validação'),
    ('aprovado', 'Aprovado'),
    ('reprovado', 'Reprovado'),
    ('pendencia', 'Pendência do usuário'),
]

STATUS_FLUXO_CIENTIFICO = [
    ('rascunho', 'Rascunho'),
    ('submetido', 'Submetido'),
    ('em_revisao', 'Em revisão'),
    ('validado', 'Validado'),
    ('rejeitado', 'Rejeitado'),
    ('necessita_revisao', 'Necessita revisão'),
]

STATUS_ENRIQUECIMENTO = [
    ("pendente", "Pendente"),
    ("parcial", "Parcialmente validado"),
    ("completo", "Completo"),
    ("falho", "Falho"),
]

# =========================================================
# MODELO PRINCIPAL: PONTOS DE PANC (registro geolocalizado)
# =========================================================
class PontoPANC(models.Model):
    nome_popular = models.CharField("Nome popular", max_length=500, blank=True)
    planta = models.ForeignKey('PlantaReferencial', on_delete=models.CASCADE)
    grupo = models.ForeignKey('Grupo', on_delete=models.SET_NULL, null=True, blank=True, related_name='pontos', verbose_name="Grupo/Comunidade")
    criado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='pontos_criados', verbose_name="Usuário que cadastrou")
    tipo_local = models.CharField("Tipo de local", max_length=20, choices=TIPOS_DE_LOCAL, default='outro')
    endereco = models.CharField("Endereço", max_length=255, blank=True, null=True)
    numero = models.CharField("Número", max_length=20, blank=True, null=True)
    bairro = models.CharField("Bairro", max_length=255, blank=True, null=True)
    cidade = models.CharField("Cidade", max_length=255, blank=True)
    estado = models.CharField("Estado", max_length=255, blank=True)
    colaborador = models.CharField("Colaborador", max_length=255, blank=True, help_text="Nome ou apelido de quem cadastrou")
    relato = models.TextField("Relato", blank=True, help_text="História, observação ou uso do local")
    foto = models.ImageField("Foto", upload_to='photos/', blank=True, null=True)
    localizacao = models.PointField("Localização", geography=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    # Identificação automatizada por IA
    nome_popular_sugerido = models.CharField("Nome popular sugerido (IA)", max_length=100, blank=True, null=True)
    nome_cientifico_sugerido = models.CharField("Nome científico sugerido (IA)", max_length=150, blank=True, null=True)
    score_identificacao = models.FloatField("Confiança da identificação automática (%)", blank=True, null=True)
    status_identificacao = models.CharField("Status da identificação", max_length=20, choices=STATUS_IDENTIFICACAO, default='pendente')

    # Validação comunitária ou especialista
    status_validacao = models.CharField("Status de validação", max_length=20, choices=STATUS_VALIDACAO, default='pendente')
    status_fluxo = models.CharField("Status do fluxo científico", max_length=20, choices=STATUS_FLUXO_CIENTIFICO, default='rascunho')
    status_enriquecimento = models.CharField("Status do enriquecimento", max_length=20, choices=STATUS_ENRIQUECIMENTO, default="pendente")
    nome_cientifico_submetido = models.CharField("Nome científico submetido", max_length=200, blank=True, null=True)
    nome_cientifico_validado = models.CharField("Nome científico validado", max_length=200, blank=True, null=True)
    nome_aceito = models.CharField("Nome aceito", max_length=200, blank=True, null=True)
    sinonimos = models.JSONField("Sinônimos", default=list, blank=True)
    autoria = models.CharField("Autoria", max_length=200, blank=True, null=True)
    fonte_taxonomica_primaria = models.CharField("Fonte taxonômica primária", max_length=120, blank=True, null=True)
    fontes_secundarias = models.JSONField("Fontes secundárias (legado)", default=list, blank=True)
    fontes_taxonomicas_secundarias = models.JSONField("Fontes taxonômicas secundárias", default=list, blank=True)
    grau_confianca = models.FloatField("Grau de confiança (legado)", default=0.0)
    grau_confianca_taxonomica = models.FloatField("Grau de confiança taxonômica", default=0.0)
    distribuicao_resumida = models.TextField("Distribuição resumida", blank=True, null=True)
    ocorrencias_gbif = models.IntegerField("Ocorrências GBIF", default=0)
    ocorrencias_inaturalist = models.IntegerField("Ocorrências iNaturalist", default=0)
    fenologia_observada = models.CharField("Fenologia observada", max_length=255, blank=True, null=True)
    imagem_url = models.URLField("Imagem URL", max_length=500, blank=True, null=True)
    imagem_fonte = models.CharField("Fonte da imagem", max_length=100, blank=True, null=True)
    licenca_imagem = models.CharField("Licença da imagem", max_length=120, blank=True, null=True)
    ultima_validacao_em = models.DateTimeField("Última validação em", blank=True, null=True)
    validacao_pendente_revisao_humana = models.BooleanField("Validação pendente de revisão humana", default=False)
    fontes_enriquecimento = models.JSONField("Fontes do enriquecimento", default=list, blank=True)
    payload_enriquecimento = models.JSONField("Payload resumido de enriquecimento", default=dict, blank=True)
    payload_resumido_validacao = models.JSONField("Payload resumido de validação", default=dict, blank=True)
    comestibilidade_status = models.CharField("Comestibilidade (status)", max_length=20, default="indeterminado")
    comestibilidade_confirmada = models.BooleanField("Comestibilidade confirmada", default=False)
    parte_comestivel_lista = models.JSONField("Partes comestíveis normalizadas", default=None, null=True, blank=True)
    parte_comestivel_confirmada = models.BooleanField("Parte comestível confirmada", default=False)
    frutificacao_meses = models.JSONField("Meses de frutificação normalizados", default=None, null=True, blank=True)
    frutificacao_confirmada = models.BooleanField("Frutificação confirmada", default=False)
    colheita_periodo = models.JSONField("Período de colheita consolidado", default=None, null=True, blank=True)
    colheita_confirmada = models.BooleanField("Colheita confirmada", default=False)
    fontes_campos_enriquecimento = models.JSONField("Fontes por campo enriquecido", default=dict, blank=True)
    integracoes_utilizadas = models.JSONField("Integrações utilizadas", default=list, blank=True)
    integracoes_com_falha = models.JSONField("Integrações com falha", default=list, blank=True)
    enriquecimento_atualizado_em = models.DateTimeField("Enriquecimento atualizado em", blank=True, null=True)
    criado_em = models.DateTimeField("Data de criação", auto_now_add=True)
    atualizado_em = models.DateTimeField("Atualizado em", auto_now=True)

    def clean(self):
        # Garante que o ponto esteja dentro do Brasil (aprox.)
        if self.localizacao:
            if not (-34 <= self.localizacao.y <= 5 and -74 <= self.localizacao.x <= -34):
                raise ValidationError({"localizacao": "A localização parece fora do Brasil. Verifique no mapa."})

    def __str__(self):
        if self.planta:
            return f"{self.planta.nome_popular} - {self.cidade or 'Local não identificado'}"
        elif self.nome_popular_sugerido:
            return f"{self.nome_popular_sugerido} (sugerido) - {self.cidade or 'Local não identificado'}"
        return f"Ponto sem planta - {self.cidade or 'Local não identificado'}"

    class Meta:
        ordering = ['-criado_em']
        indexes = [
            models.Index(fields=['cidade', 'estado']),
            models.Index(fields=['tipo_local']),
            models.Index(fields=['criado_em']),
            models.Index(fields=['grupo']),
            models.Index(fields=['status_fluxo', 'status_validacao']),
        ]
        verbose_name = "Ponto de PANC"
        verbose_name_plural = "Pontos de PANC"


class EnriquecimentoTaxonomicoHistorico(models.Model):
    ponto = models.ForeignKey("PontoPANC", on_delete=models.CASCADE, related_name="historico_enriquecimento")
    status = models.CharField(max_length=20, choices=STATUS_ENRIQUECIMENTO, default="pendente")
    grau_confianca = models.FloatField(default=0.0)
    fontes = models.JSONField(default=list, blank=True)
    payload_resumido = models.JSONField(default=dict, blank=True)
    executado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-executado_em"]

    def __str__(self):
        return f"Enriquecimento {self.ponto_id} ({self.status})"

# ======================================
# PLANTAS REFERENCIAIS (CATÁLOGO/BASE)
# ======================================
class PlantaReferencial(models.Model):
    nome_popular = models.CharField("Nome popular", max_length=200)
    nome_cientifico = models.CharField("Nome científico", max_length=200, blank=True)
    comestivel = models.BooleanField("Comestível", null=True, blank=True, default=None)
    parte_comestivel = models.CharField("Parte comestível", max_length=100, blank=True)
    epoca_frutificacao = models.CharField("Frutificação (meses)", max_length=120, blank=True, default="Não informado")
    epoca_colheita = models.CharField("Colheita (período do ano)", max_length=120, blank=True, default="Não informado")
    forma_uso = models.TextField("Forma de uso", blank=True)
    grupo_taxonomico = models.CharField("Grupo taxonômico", max_length=100, blank=True, null=True)
    origem = models.CharField("Origem", max_length=100, blank=True, null=True)
    bioma = models.CharField("Bioma", max_length=100, blank=True, null=True)
    regiao_ocorrencia = models.CharField("Região de ocorrência", max_length=100, blank=True, null=True)
    fonte = models.CharField("Fonte", max_length=255, blank=True, null=True)
    nome_cientifico_valido = models.CharField("Nome científico válido", max_length=200, blank=True, null=True)
    nome_cientifico_corrigido = models.CharField("Nome científico corrigido", max_length=200, blank=True, null=True)
    fonte_validacao = models.CharField("Fonte de validação", max_length=200, blank=True, null=True)

    # ---- Campos de enriquecimento taxonômico ----
    nome_cientifico_submetido = models.CharField("Nome científico submetido", max_length=300, blank=True, null=True)
    nome_cientifico_validado = models.CharField("Nome científico validado (Global Names)", max_length=300, blank=True, null=True)
    nome_aceito = models.CharField("Nome aceito (Tropicos)", max_length=300, blank=True, null=True)
    sinonimos = models.JSONField("Sinônimos", default=list, blank=True)
    autoria = models.CharField("Autoria", max_length=300, blank=True, null=True)
    fonte_taxonomica_primaria = models.CharField("Fonte taxonômica primária", max_length=200, blank=True, null=True)
    fontes_secundarias = models.JSONField("Fontes secundárias", default=list, blank=True)
    grau_confianca = models.FloatField("Grau de confiança do enriquecimento", blank=True, null=True, help_text="0.0 a 1.0")
    distribuicao_resumida = models.TextField("Distribuição resumida", blank=True, null=True)
    ocorrencias_gbif = models.PositiveIntegerField("Ocorrências GBIF", blank=True, null=True)
    ocorrencias_inaturalist = models.PositiveIntegerField("Ocorrências iNaturalist", blank=True, null=True)
    fenologia_observada = models.JSONField("Fenologia observada (iNaturalist)", default=dict, blank=True)
    imagem_url = models.URLField("URL da imagem de referência", max_length=500, blank=True, null=True)
    imagem_fonte = models.CharField("Fonte da imagem", max_length=200, blank=True, null=True)
    licenca_imagem = models.CharField("Licença da imagem", max_length=200, blank=True, null=True)
    ultima_validacao_em = models.DateTimeField("Última validação taxonômica", blank=True, null=True)
    status_enriquecimento = models.CharField(
        "Status do enriquecimento",
        max_length=30,
        choices=[
            ('pendente', 'Pendente'),
            ('completo', 'Completo'),
            ('parcial', 'Parcial'),
            ('erro', 'Erro'),
        ],
        default='pendente',
    )
    payload_enriquecimento = models.JSONField("Payload resumido do enriquecimento", default=dict, blank=True)
    descricao_consolidada = models.TextField("Descrição consolidada", blank=True, default="")
    descricao_resumida = models.TextField("Descrição resumida", blank=True, default="")
    nomes_populares = models.JSONField("Nomes populares consolidados", default=list, blank=True)
    aliases = models.JSONField("Aliases consolidados", default=list, blank=True)
    familia = models.CharField("Família botânica", max_length=200, blank=True, default="")
    genero = models.CharField("Gênero botânico", max_length=200, blank=True, default="")
    especie = models.CharField("Epíteto específico", max_length=200, blank=True, default="")
    toxicidade = models.CharField("Toxicidade", max_length=200, blank=True, default="")
    sazonalidade = models.JSONField("Sazonalidade estruturada", default=dict, blank=True)
    fontes_utilizadas = models.JSONField("Fontes utilizadas para ficha canônica", default=list, blank=True)
    nivel_confianca_enriquecimento = models.FloatField("Nível de confiança consolidado", default=0.0)
    is_fully_enriched = models.BooleanField("Ficha canônica totalmente enriquecida", default=False)
    enriquecimento_completo_em = models.DateTimeField("Enriquecimento completo em", blank=True, null=True)

    class Meta:
        verbose_name = "Planta referencial"
        verbose_name_plural = "Plantas referenciais"
        ordering = ['nome_popular']

    def __str__(self):
        return self.nome_popular


# =============================================
# HISTÓRICO DE ENRIQUECIMENTO TAXONÔMICO
# =============================================
class HistoricoEnriquecimento(models.Model):
    planta = models.ForeignKey(PlantaReferencial, on_delete=models.CASCADE, related_name='historico_enriquecimento')
    data = models.DateTimeField("Data do enriquecimento", auto_now_add=True)
    fontes_consultadas = models.JSONField("Fontes consultadas", default=list)
    resultado = models.JSONField("Resultado completo", default=dict)
    status = models.CharField("Status", max_length=30, choices=[
        ('completo', 'Completo'),
        ('parcial', 'Parcial'),
        ('erro', 'Erro'),
    ], default='parcial')
    erro_detalhes = models.TextField("Detalhes de erros", blank=True, null=True)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='enriquecimentos_realizados',
    )

    class Meta:
        ordering = ['-data']
        verbose_name = "Histórico de enriquecimento"
        verbose_name_plural = "Históricos de enriquecimento"

    def __str__(self):
        return f"Enriquecimento de {self.planta} em {self.data:%d/%m/%Y %H:%M}"


class PlantaAlias(models.Model):
    planta = models.ForeignKey(PlantaReferencial, on_delete=models.CASCADE, related_name="aliases_registrados")
    name = models.CharField("Alias", max_length=255)
    normalized_name = models.CharField("Alias normalizado", max_length=255, db_index=True)
    source = models.CharField("Origem do alias", max_length=100, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        unique_together = ("planta", "normalized_name")

    def __str__(self):
        return f"{self.name} -> {self.planta_id}"


# ==============================
# VALIDAÇÃO E PARECER DE PONTO
# ==============================
class ParecerValidacao(models.Model):
    ponto = models.ForeignKey('PontoPANC', on_delete=models.CASCADE, related_name='pareceres')
    especialista = models.ForeignKey(User, on_delete=models.CASCADE)
    parecer = models.CharField(max_length=10, choices=[
        ('aprovado', 'Aprovado'),
        ('reprovado', 'Reprovado'),
        ('pendencia', 'Pendência')
    ])
    comentario = models.TextField(blank=True)
    data = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('ponto', 'especialista')
        ordering = ['-data']

    def __str__(self):
        return f'{self.ponto} | {self.especialista} | {self.parecer}'

# ==============================
# INSÍGNIA / BADGE
# ==============================

class Badge(models.Model):
    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True)
    icone = models.ImageField("Ícone", upload_to='badges/', blank=True, null=True)
    data_criacao = models.DateTimeField(auto_now_add=True)
    nivel = models.PositiveIntegerField(
        default=1,
        help_text="Nível ou raridade do badge (1=comum, 2=raro, etc)"
    )
    missao = models.ForeignKey(
        'Missao',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Missão relacionada (opcional)"
    )
    unico = models.BooleanField(
        default=False,
        help_text="É um badge único para o primeiro a conquistar?"
    )

    def __str__(self):
        return f"{self.nome} (Badge)"

    class Meta:
        verbose_name = "Badge / Insígnia"
        verbose_name_plural = "Badges / Insígnias"
        ordering = ['-data_criacao']

class UsuarioBadge(models.Model):
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="usuario_badges"
    )
    badge = models.ForeignKey(
        Badge,
        on_delete=models.CASCADE,
        related_name="usuario_badges"
    )
    data_conquista = models.DateTimeField(auto_now_add=True)
    contexto = models.CharField(
        max_length=200,
        blank=True,
        help_text="Ex: Missão/Evento relacionado à conquista"
    )
    nivel_usuario = models.PositiveIntegerField(
        default=1,
        help_text="Nível do usuário no momento da conquista"
    )

    class Meta:
        verbose_name = "Conquista de Badge"
        verbose_name_plural = "Conquistas de Badge"
        unique_together = ('usuario', 'badge')
        ordering = ['-data_conquista']

    def __str__(self):
        return f"{self.usuario.username} - {self.badge.nome} em {self.data_conquista:%d/%m/%Y}"

# ==============================
# FEEDBACK (usuário → plataforma)
# ==============================


class IntegracaoMonitoramento(models.Model):
    STATUS_CHOICES = [("online", "Online"), ("degradada", "Degradada"), ("offline", "Offline")]

    nome = models.CharField(max_length=120, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="offline")
    ultimo_teste_bem_sucedido = models.DateTimeField(blank=True, null=True)
    ultimo_erro = models.TextField(blank=True, null=True)
    tempo_resposta_ms = models.IntegerField(blank=True, null=True)
    requer_chave = models.BooleanField(default=False)
    quota_limite = models.CharField(max_length=120, blank=True, null=True)
    endpoint_healthcheck = models.URLField(max_length=500, blank=True, null=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Monitoramento de integração"
        verbose_name_plural = "Monitoramento de integrações"

    def __str__(self):
        return f"{self.nome} ({self.status})"


class IntegracaoMonitoramentoLog(models.Model):
    integracao = models.ForeignKey(IntegracaoMonitoramento, on_delete=models.CASCADE, related_name="logs")
    status = models.CharField(max_length=20)
    detalhe = models.TextField(blank=True, null=True)
    tempo_resposta_ms = models.IntegerField(blank=True, null=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-criado_em"]
        verbose_name = "Log de integração"
        verbose_name_plural = "Logs de integrações"


class Feedback(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    mensagem = models.TextField()
    criado_em = models.DateTimeField(auto_now_add=True)
    ponto = models.ForeignKey('PontoPANC', on_delete=models.SET_NULL, null=True, blank=True, related_name='feedbacks')

    def __str__(self):
        return f"Feedback de {self.usuario or 'Anônimo'} ({self.criado_em:%d/%m/%Y})"

    class Meta:
        ordering = ['-criado_em']

# ==============================
# MISSÃO (colaborativa, diária etc)
# ==============================
class Missao(models.Model):
    TIPO_CHOICES = [
        ('diaria', 'Diária'),
        ('semanal', 'Semanal'),
        ('especial', 'Especial'),
        ('meta', 'Meta de Cadastro'),
        ('evento', 'Evento/Temática'),
        ('colaborativa', 'Colaborativa'),
    ]
    titulo = models.CharField("Título", max_length=150)
    descricao = models.TextField("Descrição")
    tipo = models.CharField("Tipo", max_length=20, choices=TIPO_CHOICES)
    pontos = models.PositiveIntegerField("Pontos", default=10, help_text="Pontos por completar esta missão")
    ativa = models.BooleanField("Ativa", default=True)
    meta = models.PositiveIntegerField(
        "Meta",
        default=1,
        blank=True,
        null=True,
        help_text="Quantidade necessária para completar (ex: 10 cadastros)"
    )
    secreta = models.BooleanField("Missão Secreta", default=False)
    data_inicio = models.DateField("Início", null=True, blank=True)
    data_fim = models.DateField("Término", null=True, blank=True)
    criador = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="missoes_criadas",
        verbose_name="Criador",
        help_text="Usuário que criou a missão (opcional)"
    )
    destaque = models.BooleanField("Missão em Destaque", default=False)
    data_criacao = models.DateTimeField("Criada em", auto_now_add=True)

    class Meta:
        verbose_name = "Missão"
        verbose_name_plural = "Missões"
        ordering = ['-data_inicio', '-data_criacao', 'titulo']

    def __str__(self):
        return f'{self.titulo} [{self.get_tipo_display()}]'

    def is_ativa(self):
        """Retorna True se a missão está ativa e dentro do período."""
        from django.utils import timezone
        hoje = timezone.now().date()
        if not self.ativa:
            return False
        if self.data_inicio and hoje < self.data_inicio:
            return False
        if self.data_fim and hoje > self.data_fim:
            return False
        return True


# ==============================
# HISTÓRICO DE GAMIFICAÇÃO
# ==============================
class HistoricoGamificacao(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='historico_gamificacao')
    acao = models.CharField(max_length=150)
    pontos = models.IntegerField(default=0)
    data = models.DateTimeField(auto_now_add=True)
    referencia = models.CharField(max_length=150, blank=True, help_text="ID de referência, missão, badge, ponto, evento etc.")

    def __str__(self):
        return f'{self.usuario.username} - {self.acao} (+{self.pontos} pts)'

    class Meta:
        ordering = ['-data']

# ==============================
# NÍVEL DO USUÁRIO
# ==============================
class Nivel(models.Model):
    numero = models.PositiveIntegerField(unique=True)
    nome = models.CharField(max_length=100)
    pontos_minimos = models.PositiveIntegerField()
    pontos_maximos = models.PositiveIntegerField()
    beneficios = models.TextField(blank=True)
    surpresa_oculta = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['numero']

    def __str__(self):
        return f"{self.numero} - {self.nome}"

# ==============================
# PONTUAÇÃO DO USUÁRIO
# ==============================
class PontuacaoUsuario(models.Model):
    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='pontuacao')
    pontos = models.IntegerField(default=0)
    nivel = models.ForeignKey(Nivel, on_delete=models.SET_NULL, null=True, blank=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.usuario.username} - {self.pontos} pts'

    def atualizar_nivel(self):
        niveis = Nivel.objects.order_by('numero')
        for nivel in niveis:
            if nivel.pontos_minimos <= self.pontos <= nivel.pontos_maximos:
                if self.nivel != nivel:
                    self.nivel = nivel
                    self.save(update_fields=['nivel'])
                    BotaoFlutuante.objects.filter(usuario=self.usuario).delete()
                break

# ==============================
# SUGESTÃO DE MISSÃO
# ==============================
class SugestaoMissao(models.Model):
    titulo = models.CharField(max_length=120)
    descricao = models.TextField()
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    criado_em = models.DateTimeField(auto_now_add=True)
    aprovado = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.titulo} - {self.usuario.username}"

# ==============================
# BOTÃO FLUTUANTE DE NÍVEL/NOTIFICAÇÃO
# ==============================
class BotaoFlutuante(models.Model):
    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    exibido = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    def apagar_ao_subir_nivel(self):
        self.delete()

# ==============================
# RELAÇÃO MISSÃO <-> USUÁRIO
# ==============================
class MissaoUsuario(models.Model):
    usuario = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    missao = models.ForeignKey(Missao, on_delete=models.CASCADE)
    quantidade = models.PositiveIntegerField(default=0)  # progresso do usuário
    progresso = models.PositiveIntegerField(default=0)
    completada = models.BooleanField(default=False)
    data_conclusao = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f'{self.usuario.username} - {self.missao.titulo}'

    class Meta:
        unique_together = ('missao', 'usuario')

# ==============================
# RANKING DE REVISOR (gamificação especialista)
# ==============================
class RankingRevisor(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    pontuacao = models.PositiveIntegerField(default=0)
    avaliacoes = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f'{self.usuario.username} - {self.pontuacao} pts'

    class Meta:
        ordering = ['-pontuacao']

# ==============================
# GRUPO / COMUNIDADE
# ==============================
class Grupo(models.Model):
    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True)
    pontos_totais = models.PositiveIntegerField(default=0)
    membros = models.ManyToManyField(User, related_name='grupos')

    def atualizar_pontuacao_total(self):
        total = sum(
            pu.pontos for pu in PontuacaoUsuario.objects.filter(usuario__in=self.membros.all())
        )
        self.pontos_totais = total
        self.save(update_fields=['pontos_totais'])

    def __str__(self):
        return f"{self.nome} ({self.pontos_totais} pts)"

# ===================================
# SUGESTÃO DE EXTENSÃO: EVENTOS (EXEMPLO)
# ===================================
class Evento(models.Model):
    titulo = models.CharField(max_length=200)
    descricao = models.TextField()
    data_inicio = models.DateTimeField()
    data_fim = models.DateTimeField(null=True, blank=True)
    criador = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='eventos_criados')
    participantes = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='eventos_participados', blank=True)
    pontos = models.PositiveIntegerField(default=20)
    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Evento: {self.titulo}"

# ===================================
# Modelo Django: Alerta Climático
# ===================================

from django.db import models

# Certifique-se de que PontoPANC está importado corretamente
from .models import PontoPANC

from django.db import models

class AlertaClimatico(models.Model):
    """
    Representa um alerta climático vinculado a um ponto PANC.
    Indica riscos ambientais como queimadas, enchentes, secas, entre outros.
    """

    ponto = models.ForeignKey(
        'PontoPANC',  # entre aspas se o modelo estiver abaixo ou em outro arquivo (ajusta se necessário)
        on_delete=models.CASCADE,
        related_name="alertas",
        help_text="Ponto PANC associado ao alerta"
    )

    tipo = models.CharField(
        "Tipo de alerta",
        max_length=100,
        help_text="Tipo do alerta (ex: Queimada, Enchente, Chuva Intensa, Calor Extremo)"
    )

    severidade = models.CharField(
        "Severidade",
        max_length=50,
        blank=True, null=True,
        help_text="Nível de severidade do alerta (ex: Moderado, Alto, Perigo, Observação)"
    )

    descricao = models.TextField(
        "Descrição",
        blank=True,  # Permite não preencher (opcional)
        help_text="Descrição detalhada do alerta e dos impactos esperados"
    )

    inicio = models.DateTimeField(
        "Início",
        help_text="Data e hora de início da vigência do alerta"
    )

    fim = models.DateTimeField(
        "Fim",
        help_text="Data e hora do fim da vigência do alerta"
    )

    municipio = models.CharField(
        "Município",
        max_length=100,
        blank=True, null=True,
        help_text="Município relacionado ao alerta"
    )

    uf = models.CharField(
        "UF",
        max_length=2,
        blank=True, null=True,
        help_text="UF (estado) relacionado ao alerta"
    )

    id_alerta = models.CharField(
        "ID do Alerta na fonte",
        max_length=100,
        blank=True, null=True,
        help_text="Identificador único do alerta na fonte original"
    )

    fonte = models.CharField(
        "Fonte",
        max_length=50,
        default="INMET",
        help_text="Fonte do alerta (ex: INMET, CEMADEN, Open-Meteo, Manual)"
    )

    icone = models.CharField(
        "Ícone",
        max_length=255,
        blank=True, null=True,
        help_text="URL do ícone ilustrativo do tipo de alerta"
    )

    criado_em = models.DateTimeField(
        "Criado em",
        auto_now_add=True,
        help_text="Data de registro do alerta no sistema"
    )

    class Meta:
        unique_together = ('ponto', 'tipo', 'inicio', 'fim')
        verbose_name = "Alerta Climático"
        verbose_name_plural = "Alertas Climáticos"
        ordering = ['-inicio']

    def __str__(self):
        return f"{self.tipo} - {self.ponto.nome_popular if self.ponto else ''} ({self.inicio:%d/%m/%Y} a {self.fim:%d/%m/%Y})"


class EventoMonitorado(models.Model):
    """
    Evento ambiental monitorado por ponto (desmatamento, foco de calor, incêndio etc.).
    """

    FONTE_CHOICES = [
        ("mapbiomas", "MapBiomas Alerta"),
        ("nasa_firms", "NASA FIRMS"),
        ("climatico", "Alerta Climático"),
    ]
    TIPO_CHOICES = [
        ("desmatamento", "Desmatamento"),
        ("foco_calor", "Foco de Calor"),
        ("incendio", "Incêndio"),
        ("climatico", "Climático"),
    ]
    STATUS_SYNC_CHOICES = [
        ("novo", "Novo"),
        ("atualizado", "Atualizado"),
        ("sincronizado", "Sincronizado"),
        ("erro", "Erro"),
    ]

    ponto = models.ForeignKey(
        "PontoPANC",
        on_delete=models.CASCADE,
        related_name="eventos_monitorados",
    )
    fonte = models.CharField(max_length=30, choices=FONTE_CHOICES)
    tipo_evento = models.CharField(max_length=30, choices=TIPO_CHOICES)
    external_id = models.CharField(max_length=120, blank=True, null=True)
    hash_evento = models.CharField(max_length=120, blank=True, null=True)
    titulo = models.CharField(max_length=255, blank=True, default="")
    descricao = models.TextField(blank=True, default="")
    ocorrido_em = models.DateTimeField()
    publicado_em = models.DateTimeField(blank=True, null=True)
    latitude_evento = models.FloatField(blank=True, null=True)
    longitude_evento = models.FloatField(blank=True, null=True)
    bbox = models.JSONField(blank=True, null=True)
    area_afetada_ha = models.FloatField(blank=True, null=True)
    distancia_metros = models.FloatField(blank=True, null=True)
    severidade = models.CharField(max_length=50, blank=True, default="")
    confianca = models.CharField(max_length=50, blank=True, default="")
    brilho = models.FloatField(blank=True, null=True)
    frp = models.FloatField(blank=True, null=True)
    metadata = models.JSONField(blank=True, null=True)
    status_sync = models.CharField(
        max_length=20,
        choices=STATUS_SYNC_CHOICES,
        default="sincronizado",
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Evento Monitorado"
        verbose_name_plural = "Eventos Monitorados"
        ordering = ["-ocorrido_em"]
        indexes = [
            models.Index(fields=["ponto", "fonte", "tipo_evento"]),
            models.Index(fields=["ocorrido_em"]),
            models.Index(fields=["external_id"]),
        ]
        unique_together = ("ponto", "fonte", "external_id", "ocorrido_em")

    def __str__(self):
        return f"{self.get_tipo_evento_display()} - {self.ponto_id} ({self.fonte})"



# ===================================
# SISTEMA DE NOTIFICAÇÕES PUSH
# ===================================
class DispositivoPush(models.Model):
    """
    Armazena tokens de dispositivos para notificações push (FCM/APNs)
    """
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='dispositivos_push'
    )
    token = models.CharField(
        "Token do dispositivo",
        max_length=255,
        unique=True,
        help_text="Token FCM ou APNs"
    )
    plataforma = models.CharField(
        "Plataforma",
        max_length=20,
        choices=[
            ('android', 'Android'),
            ('ios', 'iOS'),
            ('web', 'Web')
        ]
    )
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Dispositivo Push"
        verbose_name_plural = "Dispositivos Push"
        ordering = ['-atualizado_em']

    def __str__(self):
        return f"{self.usuario.username} - {self.plataforma} - {self.token[:20]}..."


class Notificacao(models.Model):
    """
    Notificações para usuários (in-app e push)
    """
    TIPO_CHOICES = [
        ('novo_ponto', 'Novo Ponto PANC'),
        ('validacao', 'Validação de Ponto'),
        ('badge', 'Nova Badge'),
        ('missao', 'Missão Completada'),
        ('nivel', 'Novo Nível'),
        ('mensagem', 'Nova Mensagem'),
        ('alerta', 'Alerta Climático'),
        ('evento', 'Novo Evento'),
        ('sistema', 'Sistema'),
    ]

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notificacoes'
    )
    tipo = models.CharField("Tipo", max_length=20, choices=TIPO_CHOICES)
    titulo = models.CharField("Título", max_length=200)
    mensagem = models.TextField("Mensagem")
    lida = models.BooleanField("Lida", default=False)
    enviada_push = models.BooleanField("Enviada via Push", default=False)

    # Metadados opcionais
    link = models.CharField(
        "Link",
        max_length=500,
        blank=True,
        help_text="Link para navegação dentro do app"
    )
    dados_extra = models.JSONField(
        "Dados Extra",
        blank=True,
        null=True,
        help_text="Dados adicionais em JSON"
    )

    criada_em = models.DateTimeField(auto_now_add=True)
    lida_em = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Notificação"
        verbose_name_plural = "Notificações"
        ordering = ['-criada_em']
        indexes = [
            models.Index(fields=['usuario', 'lida']),
            models.Index(fields=['tipo']),
        ]

    def __str__(self):
        return f"{self.usuario.username} - {self.titulo}"

    def marcar_como_lida(self):
        from django.utils import timezone
        if not self.lida:
            self.lida = True
            self.lida_em = timezone.now()
            self.save(update_fields=['lida', 'lida_em'])


# ===================================
# SISTEMA DE MENSAGENS ENTRE USUÁRIOS
# ===================================
class Conversa(models.Model):
    """
    Conversa entre dois usuários
    """
    participantes = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='conversas'
    )
    criada_em = models.DateTimeField(auto_now_add=True)
    atualizada_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Conversa"
        verbose_name_plural = "Conversas"
        ordering = ['-atualizada_em']

    def __str__(self):
        usuarios = list(self.participantes.all()[:2])
        if len(usuarios) == 2:
            return f"Conversa: {usuarios[0].username} e {usuarios[1].username}"
        return f"Conversa #{self.id}"

    def get_outro_participante(self, usuario):
        """Retorna o outro participante da conversa"""
        return self.participantes.exclude(id=usuario.id).first()


class Mensagem(models.Model):
    """
    Mensagem individual em uma conversa
    """
    conversa = models.ForeignKey(
        Conversa,
        on_delete=models.CASCADE,
        related_name='mensagens'
    )
    remetente = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='mensagens_enviadas'
    )
    conteudo = models.TextField("Conteúdo", blank=True, default="")
    lida = models.BooleanField("Lida", default=False)
    enviada_em = models.DateTimeField(auto_now_add=True)
    lida_em = models.DateTimeField(null=True, blank=True)

    # Suporte para anexos (opcional)
    imagem = models.ImageField(
        "Imagem",
        upload_to='mensagens/',
        blank=True,
        null=True
    )

    class Meta:
        verbose_name = "Mensagem"
        verbose_name_plural = "Mensagens"
        ordering = ['enviada_em']

    def __str__(self):
        return f"{self.remetente.username}: {self.conteudo[:50]}"

    def marcar_como_lida(self):
        from django.utils import timezone
        if not self.lida:
            self.lida = True
            self.lida_em = timezone.now()
            self.save(update_fields=['lida', 'lida_em'])


# ===================================
# COMPARTILHAMENTO SOCIAL
# ===================================
class CompartilhamentoSocial(models.Model):
    """
    Registro de compartilhamentos de pontos PANC em redes sociais.
    """
    CANAIS = [
        ('whatsapp', 'WhatsApp'),
        ('instagram', 'Instagram'),
        ('facebook', 'Facebook'),
        ('twitter', 'X/Twitter'),
        ('email', 'E-mail'),
        ('outro', 'Outro'),
    ]

    ponto = models.ForeignKey(
        PontoPANC,
        on_delete=models.CASCADE,
        related_name='compartilhamentos'
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='compartilhamentos',
        blank=True,
        null=True
    )
    canal = models.CharField(
        "Canal",
        max_length=20,
        choices=CANAIS,
        default='outro'
    )
    url_compartilhada = models.URLField(
        "URL compartilhada",
        blank=True
    )
    criado_em = models.DateTimeField("Criado em", auto_now_add=True)

    class Meta:
        verbose_name = "Compartilhamento social"
        verbose_name_plural = "Compartilhamentos sociais"
        ordering = ['-criado_em']

    def __str__(self):
        return f"{self.ponto_id} - {self.get_canal_display()}"


# ===================================
# RECOMENDAÇÕES DE PANCS (ML)
# ===================================
class RecomendacaoPANC(models.Model):
    """
    Recomendações personalizadas de PANCs usando Machine Learning
    """
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='recomendacoes'
    )
    planta = models.ForeignKey(
        PlantaReferencial,
        on_delete=models.CASCADE
    )
    score = models.FloatField(
        "Score de relevância",
        help_text="Pontuação de 0 a 1 indicando relevância"
    )
    razao = models.TextField(
        "Razão da recomendação",
        blank=True,
        help_text="Explicação de por que foi recomendada"
    )
    visualizada = models.BooleanField(default=False)
    criada_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Recomendação de PANC"
        verbose_name_plural = "Recomendações de PANCs"
        ordering = ['-score', '-criada_em']
        unique_together = ('usuario', 'planta')

    def __str__(self):
        return f"{self.usuario.username} - {self.planta.nome_popular} ({self.score:.2f})"


# ===================================
# INTEGRAÇÕES E-COMMERCE
# ===================================
class IntegracaoEcommerce(models.Model):
    nome = models.CharField("Nome da integração", max_length=100)
    base_url = models.URLField("URL base")
    ativo = models.BooleanField("Ativo", default=True)
    ultima_sincronizacao = models.DateTimeField(
        "Última sincronização",
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = "Integração de e-commerce"
        verbose_name_plural = "Integrações de e-commerce"
        ordering = ['nome']

    def __str__(self):
        return self.nome


class ProdutoSemente(models.Model):
    nome = models.CharField("Nome do produto", max_length=150)
    url = models.URLField("URL do produto")
    preco = models.DecimalField(
        "Preço",
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    disponivel = models.BooleanField("Disponível", default=True)
    integracao = models.ForeignKey(
        IntegracaoEcommerce,
        on_delete=models.CASCADE,
        related_name='produtos'
    )
    planta = models.ForeignKey(
        PlantaReferencial,
        on_delete=models.SET_NULL,
        related_name='produtos_semente',
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = "Produto de semente"
        verbose_name_plural = "Produtos de sementes"
        ordering = ['nome']

    def __str__(self):
        return self.nome


# ===================================
# ROTEIROS
# ===================================
class RoteiroPANC(models.Model):
    titulo = models.CharField("Título", max_length=120)
    descricao = models.TextField("Descrição", blank=True)
    criado_em = models.DateTimeField("Criado em", auto_now_add=True)
    criador = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='roteiros'
    )

    class Meta:
        verbose_name = "Roteiro PANC"
        verbose_name_plural = "Roteiros PANC"
        ordering = ['-criado_em']

    def __str__(self):
        return self.titulo


class RoteiroPANCItem(models.Model):
    roteiro = models.ForeignKey(
        RoteiroPANC,
        on_delete=models.CASCADE,
        related_name='itens'
    )
    ponto = models.ForeignKey(
        PontoPANC,
        on_delete=models.CASCADE,
        related_name='roteiros'
    )
    ordem = models.PositiveIntegerField("Ordem", default=1)
    observacao = models.CharField("Observação", max_length=200, blank=True)

    class Meta:
        verbose_name = "Item do roteiro"
        verbose_name_plural = "Itens do roteiro"
        ordering = ['ordem']
        unique_together = (('roteiro', 'ponto'),)

    def __str__(self):
        return f"{self.roteiro} - {self.ponto}"


# ===================================
# REFERÊNCIAS AR
# ===================================
class ReferenciaAR(models.Model):
    titulo = models.CharField("Título", max_length=120)
    descricao = models.TextField("Descrição", blank=True)
    asset_url = models.URLField("URL do asset", blank=True)
    criado_em = models.DateTimeField("Criado em", auto_now_add=True)
    planta = models.ForeignKey(
        PlantaReferencial,
        on_delete=models.SET_NULL,
        related_name='referencias_ar',
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = "Referência AR"
        verbose_name_plural = "Referências AR"
        ordering = ['-criado_em']

    def __str__(self):
        return self.titulo


# ===================================
# E-COMMERCE DE SEMENTES
# ===================================
class LojaExterno(models.Model):
    """
    Lojas parceiras de sementes/mudas
    """
    nome = models.CharField("Nome da Loja", max_length=200)
    descricao = models.TextField("Descrição", blank=True)
    url = models.URLField("URL do site")
    logo = models.ImageField(
        "Logo",
        upload_to='lojas/',
        blank=True,
        null=True
    )
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Loja Externa"
        verbose_name_plural = "Lojas Externas"
        ordering = ['nome']

    def __str__(self):
        return self.nome


class ProdutoExterno(models.Model):
    """
    Produtos (sementes/mudas) disponíveis em lojas parceiras
    """
    loja = models.ForeignKey(
        LojaExterno,
        on_delete=models.CASCADE,
        related_name='produtos'
    )
    planta = models.ForeignKey(
        PlantaReferencial,
        on_delete=models.CASCADE,
        related_name='produtos_disponiveis'
    )
    nome = models.CharField("Nome do Produto", max_length=200)
    descricao = models.TextField("Descrição", blank=True)
    preco = models.DecimalField(
        "Preço",
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    url_produto = models.URLField("URL do Produto")
    imagem = models.ImageField(
        "Imagem",
        upload_to='produtos/',
        blank=True,
        null=True
    )
    disponivel = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Produto Externo"
        verbose_name_plural = "Produtos Externos"
        ordering = ['nome']

    def __str__(self):
        return f"{self.nome} - {self.loja.nome}"


# ===================================
# SISTEMA DE ROTAS
# ===================================
class Rota(models.Model):
    """
    Rotas planejadas para visitar múltiplas PANCs
    """
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='rotas'
    )
    nome = models.CharField("Nome da Rota", max_length=200)
    descricao = models.TextField("Descrição", blank=True)
    pontos = models.ManyToManyField(
        PontoPANC,
        through='RotaPonto',
        related_name='rotas'
    )
    publica = models.BooleanField(
        "Pública",
        default=False,
        help_text="Permitir que outros usuários vejam esta rota"
    )
    distancia_total = models.FloatField(
        "Distância Total (km)",
        null=True,
        blank=True
    )
    tempo_estimado = models.IntegerField(
        "Tempo Estimado (minutos)",
        null=True,
        blank=True
    )
    criada_em = models.DateTimeField(auto_now_add=True)
    atualizada_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Rota"
        verbose_name_plural = "Rotas"
        ordering = ['-criada_em']

    def __str__(self):
        return f"{self.nome} - {self.usuario.username}"


class RotaPonto(models.Model):
    """
    Relacionamento ordenado entre Rota e PontoPANC
    """
    rota = models.ForeignKey(Rota, on_delete=models.CASCADE)
    ponto = models.ForeignKey(PontoPANC, on_delete=models.CASCADE)
    ordem = models.PositiveIntegerField("Ordem na rota")
    visitado = models.BooleanField("Visitado", default=False)
    data_visita = models.DateTimeField(null=True, blank=True)
    notas = models.TextField("Notas", blank=True)

    class Meta:
        verbose_name = "Ponto da Rota"
        verbose_name_plural = "Pontos da Rota"
        ordering = ['rota', 'ordem']
        unique_together = ('rota', 'ordem')

    def __str__(self):
        return f"{self.rota.nome} - Ponto {self.ordem}"


# ===================================
# CACHE OFFLINE (para sincronização)
# ===================================
class CacheOffline(models.Model):
    """
    Cache de dados para funcionamento offline do app
    """
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cache_offline'
    )
    tipo_dados = models.CharField(
        "Tipo de Dados",
        max_length=50,
        choices=[
            ('pontos', 'Pontos PANC'),
            ('plantas', 'Plantas Referenciais'),
            ('missoes', 'Missões'),
            ('perfil', 'Perfil do Usuário'),
        ]
    )
    dados = models.JSONField("Dados em JSON")
    sincronizado = models.BooleanField(default=False)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Cache Offline"
        verbose_name_plural = "Caches Offline"
        ordering = ['-atualizado_em']
        indexes = [
            models.Index(fields=['usuario', 'tipo_dados']),
        ]

    def __str__(self):
        return f"{self.usuario.username} - {self.tipo_dados}"


# ===================================
# PREFERÊNCIAS DO USUÁRIO
# ===================================
class PreferenciasUsuario(models.Model):
    """
    Preferências e configurações do usuário
    """
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='preferencias'
    )

    # Notificações
    notif_novo_ponto = models.BooleanField("Notificar novos pontos", default=True)
    notif_validacao = models.BooleanField("Notificar validações", default=True)
    notif_mensagens = models.BooleanField("Notificar mensagens", default=True)
    notif_alertas = models.BooleanField("Notificar alertas climáticos", default=True)
    notif_push = models.BooleanField("Ativar notificações push", default=True)

    # Idioma
    idioma = models.CharField(
        "Idioma",
        max_length=10,
        choices=[
            ('pt-br', 'Português (Brasil)'),
            ('en', 'English'),
            ('es', 'Español'),
        ],
        default='pt-br'
    )

    # Privacidade
    perfil_publico = models.BooleanField("Perfil público", default=True)
    mostrar_localizacao = models.BooleanField("Mostrar localização exata", default=True)
    permitir_mensagens = models.BooleanField("Permitir mensagens de outros usuários", default=True)

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Preferências do Usuário"
        verbose_name_plural = "Preferências dos Usuários"

    def __str__(self):
        return f"Preferências de {self.usuario.username}"


# ===================================
# BASE DE DADOS CUSTOMIZADA DE PLANTAS
# ===================================
class PlantaCustomizada(models.Model):
    """
    Base de dados customizada para plantas que fogem ao padrão da espécie.
    Permite criar registros específicos de variações, mutações ou características
    únicas de plantas locais.
    """
    planta_base = models.ForeignKey(
        PlantaReferencial,
        on_delete=models.CASCADE,
        related_name='variacoes_customizadas',
        help_text="Planta base de referência"
    )
    nome_variacao = models.CharField(
        "Nome da Variação",
        max_length=200,
        help_text="Ex: 'Ora-pro-nóbis de folha amarela', 'Taioba gigante do cerrado'"
    )
    descricao = models.TextField(
        "Descrição da variação",
        help_text="Características únicas que diferenciam esta variação da planta base"
    )

    # Características visuais únicas
    cor_folha = models.CharField("Cor da folha", max_length=100, blank=True)
    formato_folha = models.CharField("Formato da folha", max_length=100, blank=True)
    tamanho_medio = models.CharField("Tamanho médio", max_length=100, blank=True)
    textura = models.CharField("Textura", max_length=100, blank=True)
    cor_flor = models.CharField("Cor da flor", max_length=100, blank=True)
    epoca_floracao = models.CharField("Época de floração", max_length=100, blank=True)
    caracteristicas_especiais = models.TextField("Características especiais", blank=True)

    # Fotos de referência para identificação visual
    foto_folha = models.ImageField(
        "Foto da folha",
        upload_to='plantas_customizadas/folhas/',
        blank=True,
        null=True
    )
    foto_flor = models.ImageField(
        "Foto da flor",
        upload_to='plantas_customizadas/flores/',
        blank=True,
        null=True
    )
    foto_fruto = models.ImageField(
        "Foto do fruto",
        upload_to='plantas_customizadas/frutos/',
        blank=True,
        null=True
    )
    foto_planta_inteira = models.ImageField(
        "Foto da planta inteira",
        upload_to='plantas_customizadas/inteira/',
        blank=True,
        null=True
    )

    # Features para identificação via ML
    features_ml = models.JSONField(
        "Features para ML",
        blank=True,
        null=True,
        help_text="Características extraídas por ML para comparação (cor, textura, forma, etc)"
    )

    # Localização geográfica da variação
    regiao_encontrada = models.CharField(
        "Região onde foi encontrada",
        max_length=200,
        blank=True
    )
    clima_predominante = models.CharField(
        "Clima predominante",
        max_length=100,
        blank=True
    )

    # Dados do colaborador
    cadastrado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='plantas_customizadas'
    )
    validado_por_especialista = models.BooleanField(
        "Validado por especialista",
        default=False
    )
    especialista_validador = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='plantas_validadas'
    )

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Planta Customizada"
        verbose_name_plural = "Plantas Customizadas"
        ordering = ['-criado_em']
        indexes = [
            models.Index(fields=['planta_base', 'validado_por_especialista']),
        ]

    def __str__(self):
        return f"{self.nome_variacao} (variação de {self.planta_base.nome_popular})"


# ===================================
# MODELOS 3D PARA REALIDADE AUMENTADA
# ===================================
class ModeloAR(models.Model):
    """
    Modelos 3D e configurações para visualização em Realidade Aumentada
    """
    planta = models.ForeignKey(
        PlantaReferencial,
        on_delete=models.CASCADE,
        related_name='modelos_ar'
    )
    nome = models.CharField("Nome do modelo", max_length=200)
    descricao = models.TextField("Descrição", blank=True)

    # Arquivos do modelo 3D
    modelo_glb = models.FileField(
        "Modelo 3D (GLB/GLTF)",
        upload_to='modelos_ar/',
        help_text="Arquivo GLB ou GLTF para visualização AR"
    )
    preview_image = models.ImageField(
        "Imagem de preview",
        upload_to='modelos_ar/previews/',
        blank=True,
        null=True
    )

    # Configurações de escala e posicionamento
    escala_padrao = models.FloatField(
        "Escala padrão",
        default=1.0,
        help_text="Escala padrão do modelo (1.0 = tamanho real)"
    )
    rotacao_inicial = models.JSONField(
        "Rotação inicial",
        default=dict,
        blank=True,
        help_text="Rotação inicial do modelo em JSON {x, y, z} em graus"
    )
    posicao_inicial = models.JSONField(
        "Posição inicial",
        default=dict,
        blank=True,
        help_text="Posição inicial do modelo em JSON {x, y, z} em metros"
    )

    # Informações adicionais para AR
    animacoes_disponiveis = models.JSONField(
        "Animações disponíveis",
        default=list,
        blank=True,
        help_text="Lista de animações disponíveis no modelo"
    )
    permite_interacao = models.BooleanField(
        "Permite interação",
        default=True,
        help_text="Usuário pode rotacionar/escalar o modelo"
    )

    # Metadados
    tamanho_arquivo = models.IntegerField(
        "Tamanho do arquivo (bytes)",
        null=True,
        blank=True
    )
    formato = models.CharField(
        "Formato",
        max_length=20,
        choices=[
            ('glb', 'GLB'),
            ('gltf', 'GLTF'),
            ('usdz', 'USDZ (iOS)'),
        ],
        default='glb'
    )

    ativo = models.BooleanField("Ativo", default=True)
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Modelo AR"
        verbose_name_plural = "Modelos AR"
        ordering = ['-criado_em']

    def __str__(self):
        return f"AR: {self.planta.nome_popular} - {self.nome}"


# ===================================
# HISTÓRICO DE IDENTIFICAÇÃO
# ===================================
class HistoricoIdentificacao(models.Model):
    """
    Histórico de tentativas de identificação de plantas
    """
    METODO_CHOICES = [
        ('google_vision', 'Google Cloud Vision'),
        ('plantnet', 'PlantNet'),
        ('plantid', 'Plant.id'),
        ('custom_ml', 'Base Customizada (ML)'),
        ('manual', 'Identificação Manual'),
    ]

    ponto = models.ForeignKey(
        PontoPANC,
        on_delete=models.CASCADE,
        related_name='historico_identificacoes',
        null=True,
        blank=True
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    # Dados da identificação
    metodo = models.CharField(
        "Método de identificação",
        max_length=30,
        choices=METODO_CHOICES
    )
    imagem = models.ImageField(
        "Imagem analisada",
        upload_to='identificacoes/',
        blank=True,
        null=True
    )

    # Resultados
    planta_identificada = models.ForeignKey(
        PlantaReferencial,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='identificacoes'
    )
    planta_customizada_identificada = models.ForeignKey(
        PlantaCustomizada,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='identificacoes'
    )
    score_confianca = models.FloatField(
        "Score de confiança",
        help_text="De 0 a 100"
    )
    resultados_completos = models.JSONField(
        "Resultados completos",
        blank=True,
        null=True,
        help_text="JSON com todos os resultados da API"
    )

    # Status
    sucesso = models.BooleanField("Identificação bem-sucedida", default=True)
    erro = models.TextField("Mensagem de erro", blank=True)

    tempo_processamento = models.FloatField(
        "Tempo de processamento (segundos)",
        null=True,
        blank=True
    )

    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Histórico de Identificação"
        verbose_name_plural = "Históricos de Identificação"
        ordering = ['-criado_em']
        indexes = [
            models.Index(fields=['usuario', 'metodo']),
            models.Index(fields=['sucesso', 'metodo']),
        ]

    def __str__(self):
        if self.planta_identificada:
            return f"{self.metodo}: {self.planta_identificada.nome_popular} ({self.score_confianca:.1f}%)"
        return f"{self.metodo}: Identificação sem resultado"


class PredicaoIA(models.Model):
    RISCO_CHOICES = [
        ('alto', 'Alta confiança'),
        ('medio', 'Média confiança'),
        ('baixo', 'Baixa confiança'),
    ]

    ponto = models.ForeignKey(PontoPANC, on_delete=models.CASCADE, related_name='predicoes_ia')
    historico_identificacao = models.ForeignKey(
        HistoricoIdentificacao,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='predicoes_estruturadas',
    )
    provedor = models.CharField(max_length=30)
    predicoes_top_k = models.JSONField(default=list)
    score_confianca = models.FloatField(help_text='Score de 0 a 1')
    faixa_risco = models.CharField(max_length=10, choices=RISCO_CHOICES)
    justificativa = models.TextField(blank=True)
    requer_revisao_humana = models.BooleanField(default=True)
    fonte_predicao = models.CharField(max_length=80, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-criado_em']
        indexes = [models.Index(fields=['ponto', 'provedor', 'criado_em'])]


class ValidacaoEspecialista(models.Model):
    DECISAO_CHOICES = [
        ('validado', 'Validado'),
        ('rejeitado', 'Rejeitado'),
        ('necessita_revisao', 'Necessita revisão'),
    ]

    ponto = models.ForeignKey(PontoPANC, on_delete=models.CASCADE, related_name='validacoes_especialistas')
    revisor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='validacoes_realizadas')
    predicao_ia = models.ForeignKey(PredicaoIA, on_delete=models.SET_NULL, null=True, blank=True, related_name='validacoes')
    decisao_final = models.CharField(max_length=20, choices=DECISAO_CHOICES)
    especie_final = models.CharField(max_length=200, blank=True)
    motivo_divergencia = models.TextField(blank=True)
    observacao = models.TextField(blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-criado_em']
        indexes = [models.Index(fields=['ponto', 'decisao_final', 'criado_em'])]


class HistoricoValidacao(models.Model):
    ponto = models.ForeignKey(PontoPANC, on_delete=models.CASCADE, related_name='historico_validacoes')
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    evento = models.CharField(max_length=80)
    dados = models.JSONField(default=dict, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-criado_em']
        indexes = [models.Index(fields=['ponto', 'evento', 'criado_em'])]


class APIUsageLog(models.Model):
    api_name = models.CharField(max_length=40)
    month = models.CharField(max_length=7)
    limit = models.PositiveIntegerField(default=0)
    used = models.PositiveIntegerField(default=0)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('api_name', 'month')
        ordering = ['-month', 'api_name']


# ===================================
# SISTEMA DE PLANTAS OFFLINE SELETIVAS
# ===================================
class PacotePlantasOffline(models.Model):
    """
    Pacotes pré-definidos de plantas para download offline
    Exemplo: "PANCs do Cerrado", "PANCs da Mata Atlântica", "Iniciantes"
    """
    nome = models.CharField("Nome do Pacote", max_length=200)
    descricao = models.TextField("Descrição", help_text="Descrição do pacote de plantas")
    icone = models.ImageField(
        "Ícone",
        upload_to='pacotes_offline/',
        blank=True,
        null=True
    )
    plantas = models.ManyToManyField(
        PlantaReferencial,
        related_name='pacotes_offline',
        help_text="Plantas incluídas neste pacote"
    )
    bioma = models.CharField(
        "Bioma",
        max_length=100,
        blank=True,
        help_text="Bioma principal deste pacote"
    )
    regiao = models.CharField(
        "Região",
        max_length=100,
        blank=True,
        help_text="Região geográfica deste pacote"
    )
    dificuldade = models.CharField(
        "Dificuldade",
        max_length=20,
        choices=[
            ('iniciante', 'Iniciante'),
            ('intermediario', 'Intermediário'),
            ('avancado', 'Avançado'),
        ],
        default='iniciante'
    )
    tamanho_estimado = models.IntegerField(
        "Tamanho Estimado (MB)",
        default=0,
        help_text="Tamanho estimado do download em MB"
    )
    ativo = models.BooleanField("Ativo", default=True)
    ordem = models.IntegerField(
        "Ordem de exibição",
        default=0,
        help_text="Ordem para listar os pacotes"
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Pacote de Plantas Offline"
        verbose_name_plural = "Pacotes de Plantas Offline"
        ordering = ['ordem', 'nome']

    def __str__(self):
        return f"{self.nome} ({self.plantas.count()} plantas)"

    def calcular_tamanho(self):
        """Calcula o tamanho estimado do pacote baseado nas plantas"""
        # Estimativa: ~500KB por planta (fotos + dados)
        return self.plantas.count() * 0.5


class PlantaOfflineUsuario(models.Model):
    """
    Rastreamento de plantas baixadas por cada usuário para uso offline
    """
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='plantas_offline'
    )
    planta = models.ForeignKey(
        PlantaReferencial,
        on_delete=models.CASCADE,
        related_name='usuarios_offline'
    )

    # Status do download
    status = models.CharField(
        "Status",
        max_length=20,
        choices=[
            ('pendente', 'Pendente'),
            ('baixando', 'Baixando'),
            ('concluido', 'Concluído'),
            ('erro', 'Erro'),
        ],
        default='pendente'
    )
    progresso = models.IntegerField(
        "Progresso (%)",
        default=0,
        help_text="Progresso do download de 0 a 100"
    )

    # Dados baixados
    dados_completos = models.JSONField(
        "Dados Completos",
        blank=True,
        null=True,
        help_text="JSON com todos os dados da planta (nome, características, fotos, etc)"
    )
    fotos_baixadas = models.JSONField(
        "URLs das Fotos Baixadas",
        default=list,
        blank=True,
        help_text="Lista de URLs de fotos baixadas"
    )
    modelo_ar_baixado = models.BooleanField(
        "Modelo AR Baixado",
        default=False
    )

    # Features para identificação offline
    features_identificacao = models.JSONField(
        "Features para Identificação",
        blank=True,
        null=True,
        help_text="Features extraídas para identificação offline (histogramas, texturas, etc)"
    )

    # Metadados
    tamanho_total_mb = models.FloatField(
        "Tamanho Total (MB)",
        default=0.0,
        help_text="Tamanho total dos dados baixados em MB"
    )
    ultima_atualizacao = models.DateTimeField(
        "Última Atualização",
        null=True,
        blank=True,
        help_text="Data da última atualização dos dados"
    )
    versao_dados = models.CharField(
        "Versão dos Dados",
        max_length=50,
        blank=True,
        help_text="Versão dos dados baixados para controle de atualizações"
    )

    # Estatísticas de uso
    vezes_identificada = models.IntegerField(
        "Vezes Identificada",
        default=0,
        help_text="Quantas vezes esta planta foi identificada offline por este usuário"
    )
    ultima_identificacao = models.DateTimeField(
        "Última Identificação",
        null=True,
        blank=True
    )

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Planta Offline do Usuário"
        verbose_name_plural = "Plantas Offline dos Usuários"
        unique_together = ('usuario', 'planta')
        ordering = ['-atualizado_em']
        indexes = [
            models.Index(fields=['usuario', 'status']),
            models.Index(fields=['planta', 'status']),
        ]

    def __str__(self):
        return f"{self.usuario.username} - {self.planta.nome_popular} ({self.status})"

    def marcar_como_identificada(self):
        """Registra que esta planta foi identificada offline"""
        from django.utils import timezone
        self.vezes_identificada += 1
        self.ultima_identificacao = timezone.now()
        self.save(update_fields=['vezes_identificada', 'ultima_identificacao'])


class ConfiguracaoOffline(models.Model):
    """
    Configurações de uso offline do usuário
    """
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='config_offline'
    )

    # Configurações de download
    baixar_apenas_wifi = models.BooleanField(
        "Baixar apenas com WiFi",
        default=True,
        help_text="Fazer download apenas quando conectado ao WiFi"
    )
    qualidade_fotos = models.CharField(
        "Qualidade das Fotos",
        max_length=20,
        choices=[
            ('baixa', 'Baixa (economiza espaço)'),
            ('media', 'Média (balanceado)'),
            ('alta', 'Alta (melhor qualidade)'),
        ],
        default='media'
    )
    incluir_modelos_ar = models.BooleanField(
        "Incluir Modelos AR",
        default=False,
        help_text="Baixar modelos 3D para realidade aumentada (ocupa mais espaço)"
    )

    # Limites de armazenamento
    limite_armazenamento_mb = models.IntegerField(
        "Limite de Armazenamento (MB)",
        default=500,
        help_text="Limite máximo de espaço para dados offline"
    )
    auto_limpar_antigas = models.BooleanField(
        "Limpar Plantas Antigas Automaticamente",
        default=False,
        help_text="Remover automaticamente plantas não usadas há mais de 30 dias"
    )

    # Atualização automática
    auto_atualizar = models.BooleanField(
        "Atualizar Automaticamente",
        default=True,
        help_text="Atualizar plantas offline quando houver nova versão"
    )
    frequencia_atualizacao = models.CharField(
        "Frequência de Atualização",
        max_length=20,
        choices=[
            ('diaria', 'Diária'),
            ('semanal', 'Semanal'),
            ('mensal', 'Mensal'),
            ('manual', 'Manual'),
        ],
        default='semanal'
    )

    # Estatísticas
    espaco_usado_mb = models.FloatField(
        "Espaço Usado (MB)",
        default=0.0
    )
    total_plantas_baixadas = models.IntegerField(
        "Total de Plantas Baixadas",
        default=0
    )
    ultima_sincronizacao = models.DateTimeField(
        "Última Sincronização",
        null=True,
        blank=True
    )

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Configuração Offline"
        verbose_name_plural = "Configurações Offline"

    def __str__(self):
        return f"Config Offline: {self.usuario.username}"

    def atualizar_estatisticas(self):
        """Atualiza as estatísticas de uso"""
        plantas = PlantaOfflineUsuario.objects.filter(
            usuario=self.usuario,
            status='concluido'
        )
        self.total_plantas_baixadas = plantas.count()
        self.espaco_usado_mb = sum(p.tamanho_total_mb for p in plantas)
        self.save(update_fields=['total_plantas_baixadas', 'espaco_usado_mb'])

    def verificar_limite_armazenamento(self):
        """Verifica se está próximo do limite de armazenamento"""
        self.atualizar_estatisticas()
        return self.espaco_usado_mb >= (self.limite_armazenamento_mb * 0.9)  # 90% do limite
