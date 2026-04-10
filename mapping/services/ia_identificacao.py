from dataclasses import dataclass
from typing import List, Dict

from mapping.identificacao_api import identificar_plantnet, identificar_plantid


@dataclass
class IAResultado:
    provedor: str
    top_k: List[Dict]
    score: float
    faixa_risco: str
    justificativa: str
    requer_revisao_humana: bool
    fonte_predicao: str


def _faixa_risco(score: float) -> str:
    if score >= 0.85:
        return 'alto'
    if score >= 0.6:
        return 'medio'
    return 'baixo'


def _justificativa(score: float, provedor: str) -> str:
    if score >= 0.85:
        return f'Predição de alta confiança pelo provedor {provedor}. Ainda assim recomenda-se validação comunitária.'
    if score >= 0.6:
        return f'Predição de confiança intermediária pelo provedor {provedor}. Revisão humana recomendada.'
    return f'Predição de baixa confiança pelo provedor {provedor}. Revisão humana obrigatória.'


def identificar_com_multiplos_provedores(foto, plantid_api_key: str = '') -> IAResultado | None:
    candidatos = []

    resultado_plantnet = identificar_plantnet(foto)
    if resultado_plantnet:
        candidatos.append(resultado_plantnet)

    if plantid_api_key:
        resultado_plantid = identificar_plantid(foto, plantid_api_key)
        if resultado_plantid:
            candidatos.append(resultado_plantid)

    if not candidatos:
        return None

    candidatos = sorted(candidatos, key=lambda x: x.get('score', 0), reverse=True)
    melhor = candidatos[0]
    score = float(melhor.get('score') or 0)
    faixa = _faixa_risco(score)

    top_k = [
        {
            'nome_popular': c.get('nome_popular', ''),
            'nome_cientifico': c.get('nome_cientifico', ''),
            'score': c.get('score', 0),
            'fonte': c.get('fonte', ''),
        }
        for c in candidatos[:3]
    ]

    return IAResultado(
        provedor=melhor.get('fonte', 'desconhecido'),
        top_k=top_k,
        score=score,
        faixa_risco=faixa,
        justificativa=_justificativa(score, melhor.get('fonte', 'desconhecido')),
        requer_revisao_humana=faixa != 'alto',
        fonte_predicao='servico_ia_identificacao_v1',
    )
