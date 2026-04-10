def revisor_status(request):
    """Adiciona is_revisor ao contexto de todos os templates"""
    user = request.user
    is_revisor = user.is_authenticated and (user.is_superuser or user.groups.filter(name='Revisores').exists())
    return {'is_revisor': is_revisor}
