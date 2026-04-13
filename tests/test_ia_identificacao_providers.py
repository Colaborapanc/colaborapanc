from mapping.services.ia_identificacao import identificar_com_multiplos_provedores
from mapping.services.ia_identificacao.factory import build_providers
from mapping.services.ia_identificacao.schemas import ResultadoInferencia, PredicaoNormalizada
from mapping.services.ia_identificacao import _faixa_risco


def test_faixa_risco_compatibilidade():
    assert _faixa_risco(0.9) == 'alto'
    assert _faixa_risco(0.61) == 'medio'
    assert _faixa_risco(0.1) == 'baixo'


def test_factory_retorna_providers():
    providers = build_providers(plantid_api_key='abc')
    nomes = [p.provider_name for p in providers]
    assert 'plantnet' in nomes
    assert 'plantid' in nomes


def test_identificar_com_multiplos_provedores_sem_resultado(monkeypatch):
    monkeypatch.setattr('mapping.services.ia_identificacao.build_providers', lambda plantid_api_key='': [])
    monkeypatch.setattr('mapping.services.ia_identificacao.executar_inferencia', lambda foto, providers: None)
    assert identificar_com_multiplos_provedores(foto='fake.jpg') is None


def test_identificar_com_multiplos_provedores_normaliza_saida(monkeypatch):
    resultado = ResultadoInferencia(
        sucesso=True,
        provedor='plantnet',
        predicoes=[PredicaoNormalizada(nome_popular='Ora-pro-nóbis', nome_cientifico='Pereskia aculeata', score=0.82, fonte='PlantNet')],
        confianca_geral=0.82,
        faixa_confianca='media',
        justificativa='Semelhança moderada',
        recomendacao_operacional='exigir revisão humana',
        requer_revisao_humana=True,
    )

    monkeypatch.setattr('mapping.services.ia_identificacao.build_providers', lambda plantid_api_key='': ['mock'])
    monkeypatch.setattr('mapping.services.ia_identificacao.executar_inferencia', lambda foto, providers: resultado)

    dado = identificar_com_multiplos_provedores(foto='fake.jpg')
    assert dado is not None
    assert dado.provedor == 'plantnet'
    assert dado.top_k[0]['nome_cientifico'] == 'Pereskia aculeata'
    assert dado.requer_revisao_humana is True
