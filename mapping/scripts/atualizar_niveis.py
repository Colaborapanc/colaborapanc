from mapping.models import PontuacaoUsuario, Nivel

usuarios = PontuacaoUsuario.objects.all()
niveis = Nivel.objects.all()

for usuario in usuarios:
    pontos = usuario.pontuacao
    nivel_correspondente = niveis.filter(
        pontos_minimos__lte=pontos,
        pontos_maximos__gte=pontos
    ).first()

    if nivel_correspondente:
        if usuario.nivel != nivel_correspondente:
            usuario.nivel = nivel_correspondente
            usuario.save()
            print(f"?? Usuário {usuario.usuario.username} atualizado para nível '{nivel_correspondente.nome}'")
        else:
            print(f"?? Usuário {usuario.usuario.username} já está no nível correto.")
    else:
        print(f"?? Nenhum nível encontrado para {usuario.usuario.username} com {pontos} pontos.")
