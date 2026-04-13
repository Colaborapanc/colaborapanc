from .schemas import ResultadoInferencia, PredicaoNormalizada
from .factory import build_providers
from .utils import classificar_confianca, recomendacao_operacional_por_confianca, requer_revisao_humana


def _faixa_risco(score: float) -> str:
    faixa = classificar_confianca(score)
    return 'alto' if faixa == 'alta' else ('medio' if faixa == 'media' else 'baixo')


def executar_inferencia(foto, providers):
    resultados = []
    for provider in providers:
        resultado = provider.inferir(foto)
        resultados.append(resultado)

    validos = [r for r in resultados if r.sucesso and r.predicoes]
    if not validos:
        return None

    validos.sort(key=lambda r: r.confianca_geral, reverse=True)
    melhor = validos[0]
    top_k = []
    for r in validos:
        top_k.extend(r.predicoes)

    top_k = sorted(top_k, key=lambda x: x.score, reverse=True)[:3]
    melhor.predicoes = top_k
    melhor.requer_revisao_humana = requer_revisao_humana(melhor.confianca_geral)
    melhor.recomendacao_operacional = recomendacao_operacional_por_confianca(melhor.faixa_confianca)
    return melhor


class IAResultado:
    def __init__(self, provedor, top_k, score, faixa_risco, justificativa, requer_revisao_humana, fonte_predicao):
        self.provedor = provedor
        self.top_k = top_k
        self.score = score
        self.faixa_risco = faixa_risco
        self.justificativa = justificativa
        self.requer_revisao_humana = requer_revisao_humana
        self.fonte_predicao = fonte_predicao


def identificar_com_multiplos_provedores(foto, plantid_api_key: str = ''):
    providers = build_providers(plantid_api_key=plantid_api_key)
    resultado = executar_inferencia(foto, providers)
    if not resultado:
        return None

    return IAResultado(
        provedor=resultado.provedor,
        top_k=[
            {
                'nome_popular': p.nome_popular,
                'nome_cientifico': p.nome_cientifico,
                'score': p.score,
                'fonte': p.fonte,
            }
            for p in resultado.predicoes
        ],
        score=resultado.confianca_geral,
        faixa_risco=_faixa_risco(resultado.confianca_geral),
        justificativa=resultado.justificativa,
        requer_revisao_humana=resultado.requer_revisao_humana,
        fonte_predicao='ia_identificacao_provider_v2',
    )
