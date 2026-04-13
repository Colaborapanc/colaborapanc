# mapping/utils/adicionar_pontos.py

from mapping.models import PontuacaoUsuario, HistoricoGamificacao

def adicionar_pontos(usuario, pontos, acao, referencia=None):
    """
    Soma pontos ao usuário e registra histórico de gamificação.
    """
    if not usuario:
        return

    pontuacao, created = PontuacaoUsuario.objects.get_or_create(usuario=usuario)
    pontuacao.pontos += pontos
    pontuacao.save()
    HistoricoGamificacao.objects.create(
        usuario=usuario,
        acao=acao,
        pontos=pontos,
        referencia=referencia or ""
    )
