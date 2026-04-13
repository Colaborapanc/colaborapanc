# mapping/context_processors.py

def permissoes_usuario(request):
    """
    Adiciona variáveis de contexto globais para permissões de usuário.
    is_revisor: True se o usuário pertence ao grupo 'Revisor'
    is_admin: True se o usuário é superusuário
    """
    user = request.user
    is_revisor = False
    is_admin = False

    if user.is_authenticated:
        is_admin = user.is_superuser
        # Para ser revisor, use um grupo chamado 'Revisor'
        is_revisor = user.groups.filter(name='Revisor').exists() or is_admin

    return {
        'is_revisor': is_revisor,
        'is_admin': is_admin,
    }
