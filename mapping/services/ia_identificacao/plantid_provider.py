from mapping.identificacao_api import identificar_plantid
from .base import BaseIdentificacaoProvider
from .schemas import ResultadoInferencia, PredicaoNormalizada
from .utils import classificar_confianca, recomendacao_operacional_por_confianca, justificativa_padrao


class PlantIdProvider(BaseIdentificacaoProvider):
    provider_name = 'plantid'

    def __init__(self, api_key: str = ''):
        self.api_key = api_key

    def inferir(self, foto) -> ResultadoInferencia:
        if not self.api_key:
            return ResultadoInferencia(
                sucesso=False,
                provedor=self.provider_name,
                predicoes=[],
                confianca_geral=0,
                faixa_confianca='baixa',
                justificativa='Plant.id indisponível: chave não configurada.',
                recomendacao_operacional='resultado incerto',
                requer_revisao_humana=True,
                erro='missing_api_key',
            )

        bruto = identificar_plantid(foto, self.api_key)
        if not bruto:
            return ResultadoInferencia(
                sucesso=False,
                provedor=self.provider_name,
                predicoes=[],
                confianca_geral=0,
                faixa_confianca='baixa',
                justificativa='Plant.id não retornou predições válidas.',
                recomendacao_operacional='resultado incerto',
                requer_revisao_humana=True,
                erro='sem_resultados',
            )

        score = float(bruto.get('score') or 0)
        pred = PredicaoNormalizada(
            nome_popular=bruto.get('nome_popular', ''),
            nome_cientifico=bruto.get('nome_cientifico', ''),
            score=score,
            fonte=bruto.get('fonte', 'Plant.id'),
        )
        return ResultadoInferencia(
            sucesso=True,
            provedor=self.provider_name,
            predicoes=[pred],
            confianca_geral=score,
            faixa_confianca=classificar_confianca(score),
            justificativa=justificativa_padrao('Plant.id', score),
            recomendacao_operacional=recomendacao_operacional_por_confianca(classificar_confianca(score)),
            requer_revisao_humana=True,
            bruto=bruto,
        )
