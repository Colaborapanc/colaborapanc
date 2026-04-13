from django.utils import timezone

from mapping.domains.scientific.quality_protocol import avaliar_qualidade_minima_ponto
from mapping.domains.territorial.prioritization import calcular_score_prioridade
from mapping.services.priorizacao_territorial import calcular_score_prioridade as calcular_score_prioridade_legado


class DummyPonto:
    def __init__(self, criado_em, status_validacao='pendente'):
        self.criado_em = criado_em
        self.status_validacao = status_validacao


def test_priorizacao_v1_mantem_compatibilidade_legacy_import():
    ponto = DummyPonto(timezone.now(), status_validacao='aprovado')
    novo = calcular_score_prioridade(ponto, clima_snapshot={'risco': 0.8}, densidade_validacoes=3, versao='v1')
    legado = calcular_score_prioridade_legado(ponto, clima_snapshot={'risco': 0.8}, densidade_validacoes=3)

    assert novo.score == legado.score
    assert novo.componentes['versao'] == 'v1'


def test_priorizacao_v2_expoe_componentes_auditaveis():
    ponto = DummyPonto(timezone.now(), status_validacao='reprovado')
    resultado = calcular_score_prioridade(ponto, clima_snapshot={'risco': 0.9}, densidade_validacoes=5, versao='v2')

    assert resultado.componentes['versao'] == 'v2'
    assert 'pesos' in resultado.componentes
    assert resultado.componentes['confiabilidade'] == 0.2


def test_protocolo_qualidade_minima():
    ruim = avaliar_qualidade_minima_ponto(latitude=None, longitude=None, nome_popular='', nome_cientifico='')
    assert not ruim.aprovado
    assert ruim.nivel_confianca == 'baixa'

    bom = avaliar_qualidade_minima_ponto(latitude=-12.5, longitude=-45.1, nome_popular='Ora-pro-nobis', nome_cientifico='Pereskia aculeata')
    assert bom.aprovado
    assert bom.nivel_confianca == 'alta'
