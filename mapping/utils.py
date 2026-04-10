from django.db.models import Sum
from django.utils import timezone
from .models import PontuacaoUsuario, HistoricoGamificacao, Missao, MissaoUsuario

# ============================
# Adiciona pontos ao usuário e registra histórico
# ============================
def adicionar_pontos(usuario, pontos, acao, referencia=''):
    """
    Soma pontos ao usuário, salva histórico e garante atualização da pontuação.
    """
    if not usuario:
        return
    pontuacao, _ = PontuacaoUsuario.objects.get_or_create(usuario=usuario)
    pontuacao.pontos += pontos
    pontuacao.save()
    HistoricoGamificacao.objects.create(
        usuario=usuario,
        acao=acao,
        pontos=pontos,
        referencia=referencia
    )

# ============================
# Limita pontuação de criação de desafio/missão por usuário (exemplo: no máximo 100 pontos/dia)
# ============================
def pontos_disponiveis_para_criador(usuario):
    hoje = timezone.now().date()
    total_hoje = HistoricoGamificacao.objects.filter(
        usuario=usuario,
        acao="Criou Desafio",
        data__date=hoje
    ).aggregate(total=Sum('pontos'))['total'] or 0
    return max(0, 100 - total_hoje)

# ============================
# Função centralizada para atualizar progresso e concluir missões dinâmicas
# ============================
def registrar_acao_gamificada(usuario, tipo_acao, quantidade=1, referencia_extra=None):
    """
    Atualiza progresso e conclusão automática de missões relacionadas a 'tipo_acao'.
    Exemplo de tipo_acao: 'cadastro', 'feedback', 'revisor', etc.
    """
    if not usuario:
        return

    missoes_ativas = Missao.objects.filter(tipo=tipo_acao, ativa=True)
    for missao in missoes_ativas:
        mu, created = MissaoUsuario.objects.get_or_create(usuario=usuario, missao=missao)
        if not mu.completada:
            mu.quantidade += quantidade
            if mu.quantidade >= missao.meta:
                mu.completada = True
                mu.data_conclusao = timezone.now()
                # Pontuação da missão só é atribuída uma vez!
                adicionar_pontos(
                    usuario=usuario,
                    pontos=missao.pontos,
                    acao=f"Missão concluída: {missao.titulo}",
                    referencia=f"Missao:{missao.id}"
                )
                # Exemplo: Aqui pode adicionar badges automáticos!
                # ex: atribuir_badge_automatica(usuario, missao)
            mu.save()

# ============================
# (Exemplo) Função para atribuir badge automática (expanda como preferir)
# ============================
def atribuir_badge_automatica(usuario, missao=None, nome_badge=None, descricao=None, nivel=1):
    """
    Atribui uma badge para o usuário se ainda não tiver.
    """
    from .models import Badge
    if nome_badge and not Badge.objects.filter(usuario=usuario, nome=nome_badge).exists():
        Badge.objects.create(
            usuario=usuario,
            nome=nome_badge,
            descricao=descricao or f"Conquista relacionada à missão {missao.titulo if missao else ''}",
            nivel=nivel,
            missao=missao
        )

# ============================
# Consulta pontuação total do usuário (ex: para painel, leaderboard)
# ============================
def pontuacao_total(usuario):
    if not usuario:
        return 0
    pontuacao = PontuacaoUsuario.objects.filter(usuario=usuario).first()
    return pontuacao.pontos if pontuacao else 0

# ============================
# Consulta histórico de ações gamificadas
# ============================
def historico_gamificacao(usuario, limit=20):
    return HistoricoGamificacao.objects.filter(usuario=usuario).order_by('-data')[:limit]

