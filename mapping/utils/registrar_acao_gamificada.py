# mapping/utils/registrar_acao_gamificada.py
from ..models import Missao, MissaoUsuario
from django.utils import timezone

def registrar_acao_gamificada(usuario, tipo_acao):
    """
    Atualiza progresso de missões do tipo_acao para o usuário.
    """
    missoes = Missao.objects.filter(tipo=tipo_acao, ativa=True)
    for missao in missoes:
        mu, _ = MissaoUsuario.objects.get_or_create(usuario=usuario, missao=missao)
        if not mu.completada:
            mu.quantidade += 1
            if mu.quantidade >= missao.meta:
                mu.completada = True
                mu.data_conclusao = timezone.now()
                mu.save()
