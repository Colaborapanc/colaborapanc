from mapping.services.priorizacao_territorial import calcular_score_prioridade
from mapping.services.ia_identificacao import _faixa_risco


class DummyPonto:
    def __init__(self, criado_em, status_validacao='pendente'):
        self.criado_em = criado_em
        self.status_validacao = status_validacao


def test_faixa_risco():
    assert _faixa_risco(0.9) == 'alto'
    assert _faixa_risco(0.7) == 'medio'
    assert _faixa_risco(0.2) == 'baixo'


def test_score_prioridade( monkeypatch=None):
    from django.utils import timezone
    ponto = DummyPonto(timezone.now(), status_validacao='aprovado')
    resultado = calcular_score_prioridade(ponto, clima_snapshot={'risco': 0.8}, densidade_validacoes=3)
    assert 0 <= resultado.score <= 1
    assert 'incidencia' in resultado.componentes
