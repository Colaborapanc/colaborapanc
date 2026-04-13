def classificar_confianca(score: float) -> str:
    if score >= 0.85:
        return 'alta'
    if score >= 0.6:
        return 'media'
    return 'baixa'


def recomendacao_operacional_por_confianca(faixa: str) -> str:
    if faixa == 'alta':
        return 'aceitável para revisão'
    if faixa == 'media':
        return 'exigir revisão humana'
    return 'resultado incerto'


def requer_revisao_humana(score: float) -> bool:
    return classificar_confianca(score) != 'alta'


def justificativa_padrao(provedor: str, score: float) -> str:
    faixa = classificar_confianca(score)
    if faixa == 'alta':
        return f'Predição de alta confiança via {provedor}. Recomendado confirmar por revisor humano.'
    if faixa == 'media':
        return f'Predição de confiança moderada via {provedor}. Revisão humana necessária.'
    return f'Predição de baixa confiança via {provedor}. Resultado incerto, exigir revisão humana.'
