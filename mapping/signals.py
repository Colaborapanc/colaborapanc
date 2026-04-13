import logging
import os

from django.db.models.signals import post_save, m2m_changed, post_migrate
from django.db import transaction
from django.dispatch import receiver
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from .models import (
    MissaoUsuario, PontuacaoUsuario, HistoricoGamificacao, Feedback,
    PontoPANC, Badge, Missao, Evento, Grupo, Nivel, UsuarioBadge
)
from django.utils import timezone
from mapping.services.environmental_monitor_service import EnvironmentalMonitorService

User = get_user_model()
logger = logging.getLogger(__name__)


def _resolve_site_domain() -> str:
    """Resolve domínio canônico do Site priorizando env vars de deploy."""
    explicit_domain = (
        os.environ.get("DJANGO_SITE_DOMAIN")
        or os.environ.get("DJANGO_DOMAIN")
        or os.environ.get("SITE_DOMAIN")
        or ""
    ).strip()
    if explicit_domain:
        return explicit_domain

    for host in settings.ALLOWED_HOSTS:
        if host and host not in {"localhost", "127.0.0.1", "0.0.0.0"} and not host.startswith("."):
            return host
    return "localhost"


@receiver(post_migrate)
def ensure_current_site(sender, **kwargs):
    """
    Garante que o Site necessário pelo django-allauth exista após migrations.
    Evita erro `Site matching query does not exist` em /accounts/login/.
    """
    site_id = int(getattr(settings, "SITE_ID", 1))
    domain = _resolve_site_domain()
    site_name = (os.environ.get("DJANGO_SITE_NAME") or domain).strip() or domain

    Site.objects.update_or_create(
        id=site_id,
        defaults={"domain": domain, "name": site_name},
    )

# ===========
# UTILIDADES
# ===========
def adicionar_pontos(usuario, pontos, acao, referencia=None, maximo=None):
    """Adiciona pontos, atualiza nível, histórico e badges."""
    if not usuario:
        return
    pontuacao, _ = PontuacaoUsuario.objects.get_or_create(usuario=usuario)
    pontos_adicionar = pontos

    if maximo is not None:
        pontos_adicionar = min(pontos_adicionar, maximo)

    pontuacao.pontos += pontos_adicionar
    pontuacao.save()
    pontuacao.atualizar_nivel()
    HistoricoGamificacao.objects.create(
        usuario=usuario,
        acao=acao,
        pontos=pontos_adicionar,
        referencia=referencia or ""
    )
    # Desbloqueia badges automáticos de pontos (se existir)
    for badge in Badge.objects.filter(nivel__lte=pontuacao.pontos):
        if not UsuarioBadge.objects.filter(usuario=usuario, badge=badge).exists():
            UsuarioBadge.objects.create(usuario=usuario, badge=badge, nivel_usuario=pontuacao.nivel.numero if pontuacao.nivel else 1)
            HistoricoGamificacao.objects.create(
                usuario=usuario,
                acao=f"Conquista automática: {badge.nome}",
                pontos=0,
                referencia=f"Badge:{badge.id}"
            )


# ======================================
# Missão concluída (automaticamente!)
# ======================================
@receiver(post_save, sender=MissaoUsuario)
def pontuar_missao_concluida(sender, instance, created, **kwargs):
    if getattr(instance, 'completada', False) and instance.data_conclusao:
        if not HistoricoGamificacao.objects.filter(
            usuario=instance.usuario,
            referencia=f"Missao:{instance.missao.id}"
        ).exists():
            pontos = instance.missao.pontos
            if instance.missao.tipo == "colaborativa":
                pontos = min(pontos, 100)
            adicionar_pontos(
                usuario=instance.usuario,
                pontos=pontos,
                acao=f"Missão concluída: {instance.missao.titulo}",
                referencia=f"Missao:{instance.missao.id}",
                maximo=100 if instance.missao.tipo == "colaborativa" else None
            )


# ======================================
# Cadastro de ponto PANC
# ======================================
@receiver(post_save, sender=PontoPANC)
def pontuar_novo_ponto(sender, instance, created, **kwargs):
    if created and instance.criado_por:
        adicionar_pontos(
            usuario=instance.criado_por,
            pontos=10,
            acao="Cadastro de novo ponto",
            referencia=f"Ponto:{instance.id}"
        )
        atualizar_missoes_usuario(instance.criado_por, acao="cadastro_ponto")


@receiver(post_save, sender=PontoPANC)
def sincronizar_incidentes_novo_ponto(sender, instance, created, **kwargs):
    """
    Ao cadastrar um novo ponto, sincroniza automaticamente os incidentes
    ambientais da região para compor o histórico inicial do ponto.
    """
    if not created:
        return

    def _sync_incidentes():
        try:
            EnvironmentalMonitorService().sync(
                ponto_id=instance.id,
                days=365,
                latest_only=True,
            )
        except Exception as exc:
            logger.warning("Falha ao sincronizar incidentes ambientais no pós-cadastro do ponto=%s: %s", instance.id, exc)

    transaction.on_commit(_sync_incidentes)


# ======================================
# Validação de ponto por revisor
# ======================================
@receiver(post_save, sender=PontoPANC)
def pontuar_validacao_ponto(sender, instance, created, **kwargs):
    if not created and getattr(instance, "status_validacao", None) == "aprovado":
        # Adapte para seu modelo de pareceres!
        pareceres = getattr(instance, "pareceres", None)
        if pareceres:
            for parecer in pareceres.all():
                adicionar_pontos(
                    usuario=parecer.especialista,
                    pontos=5,
                    acao="Validação de ponto aprovada",
                    referencia=f"Validacao:{instance.id}"
                )
                atualizar_missoes_usuario(parecer.especialista, acao="validacao")


# ======================================
# Envio de feedback
# ======================================
@receiver(post_save, sender=Feedback)
def pontuar_feedback(sender, instance, created, **kwargs):
    if created and instance.usuario:
        adicionar_pontos(
            usuario=instance.usuario,
            pontos=2,
            acao="Feedback enviado",
            referencia=f"Feedback:{instance.id}"
        )
        atualizar_missoes_usuario(instance.usuario, acao="feedback")


# ======================================
# Badge/Conquista atribuída (criação via UsuarioBadge)
# ======================================
@receiver(post_save, sender=UsuarioBadge)
def registrar_novo_badge(sender, instance, created, **kwargs):
    if created:
        HistoricoGamificacao.objects.create(
            usuario=instance.usuario,
            acao=f"Conquista obtida: {instance.badge.nome}",
            pontos=0,
            referencia=f"Badge:{instance.badge.id}"
        )


# ======================================
# Criação de evento especial
# ======================================
try:
    @receiver(post_save, sender=Evento)
    def pontuar_evento(sender, instance, created, **kwargs):
        if created and getattr(instance, "criador", None):
            adicionar_pontos(
                usuario=instance.criador,
                pontos=20,
                acao="Evento criado",
                referencia=f"Evento:{instance.id}"
            )
            atualizar_missoes_usuario(instance.criador, acao="evento")
except ImportError:
    pass


# ======================================
# Entrada em grupo/comunidade
# ======================================
@receiver(m2m_changed, sender=Grupo.membros.through)
def pontuar_entrada_grupo(sender, instance, action, pk_set, **kwargs):
    if action == 'post_add':
        for user_id in pk_set:
            usuario = User.objects.get(pk=user_id)
            adicionar_pontos(
                usuario=usuario,
                pontos=5,
                acao=f"Entrou no grupo: {instance.nome}",
                referencia=f"Grupo:{instance.id}"
            )


# ======================================
# Subida de nível do usuário (níveis automáticos)
# ======================================
@receiver(post_save, sender=PontuacaoUsuario)
def registrar_subida_nivel(sender, instance, **kwargs):
    if instance.nivel:
        nivel_str = f"{instance.nivel.numero} - {instance.nivel.nome}"
        ultimo = HistoricoGamificacao.objects.filter(
            usuario=instance.usuario,
            acao__startswith="Subiu para o nível"
        ).order_by('-data').first()
        if not ultimo or nivel_str not in ultimo.acao:
            HistoricoGamificacao.objects.create(
                usuario=instance.usuario,
                acao=f"Subiu para o nível: {nivel_str}",
                pontos=0,
                referencia=f"Nivel:{instance.nivel.id}"
            )


# ======================================
# Função: Atualiza automaticamente progresso de missões
# ======================================
def atualizar_missoes_usuario(usuario, acao="cadastro_ponto"):
    """Atualiza status e progresso das missões para o usuário."""
    from .models import Missao, MissaoUsuario
    hoje = timezone.now().date()
    semana_atual = hoje - timezone.timedelta(days=7)
    missoes_ativas = Missao.objects.filter(ativa=True)
    for missao in missoes_ativas:
        progresso = 0
        meta = missao.meta or 1
        # Calcula progresso conforme tipo
        if missao.tipo == 'diaria':
            progresso = PontoPANC.objects.filter(criado_por=usuario, criado_em__date=hoje).count()
        elif missao.tipo == 'semanal':
            progresso = PontoPANC.objects.filter(criado_por=usuario, criado_em__date__gte=semana_atual).count()
        elif missao.tipo == 'meta':
            progresso = PontoPANC.objects.filter(criado_por=usuario).count()
        elif missao.tipo == 'especial' and acao == "feedback":
            progresso = Feedback.objects.filter(usuario=usuario).count()
        # Para outros tipos de ação, amplie conforme sua lógica

        mu, _ = MissaoUsuario.objects.get_or_create(usuario=usuario, missao=missao)
        if progresso >= meta and not mu.completada:
            mu.progresso = progresso
            mu.completada = True
            mu.data_conclusao = timezone.now()
            mu.save()
        else:
            mu.progresso = progresso
            mu.save()
