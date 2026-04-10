from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from django.utils import timezone


@dataclass(frozen=True)
class PriorizacaoResultado:
    score: float
    componentes: dict[str, Any]
    explicacao: str


@dataclass(frozen=True)
class PriorizacaoConfig:
    versao: str
    peso_incidencia: float
    peso_clima: float
    peso_confiabilidade: float
    peso_recencia: float


V1_CONFIG = PriorizacaoConfig(
    versao="v1",
    peso_incidencia=0.30,
    peso_clima=0.25,
    peso_confiabilidade=0.25,
    peso_recencia=0.20,
)

V2_CONFIG = PriorizacaoConfig(
    versao="v2",
    peso_incidencia=0.28,
    peso_clima=0.27,
    peso_confiabilidade=0.30,
    peso_recencia=0.15,
)


class PriorizadorTerritorial:
    """Motor versionado de priorização territorial.

    Compatibilidade: o modo `v1` replica a heurística original.
    `v2` prepara evolução calibrável mantendo rastreabilidade dos componentes.
    """

    def calcular(
        self,
        ponto,
        *,
        clima_snapshot: dict[str, Any] | None = None,
        densidade_validacoes: int = 0,
        versao: str = "v1",
    ) -> PriorizacaoResultado:
        clima_snapshot = clima_snapshot or {}
        if versao == "v1":
            return self._calcular_v1(ponto, clima_snapshot, densidade_validacoes)
        if versao == "v2":
            return self._calcular_v2(ponto, clima_snapshot, densidade_validacoes)
        raise ValueError(f"Versão de score não suportada: {versao}")

    def _calcular_v1(self, ponto, clima_snapshot: dict[str, Any], densidade_validacoes: int) -> PriorizacaoResultado:
        return self._calcular_generico(
            ponto,
            clima_snapshot=clima_snapshot,
            densidade_validacoes=densidade_validacoes,
            config=V1_CONFIG,
            explicacao=(
                "Score territorial composto por incidência local (30%), risco climático (25%), "
                "confiabilidade dos dados (25%) e recência das observações (20%)."
            ),
            ajuste_v2=False,
        )

    def _calcular_v2(self, ponto, clima_snapshot: dict[str, Any], densidade_validacoes: int) -> PriorizacaoResultado:
        return self._calcular_generico(
            ponto,
            clima_snapshot=clima_snapshot,
            densidade_validacoes=densidade_validacoes,
            config=V2_CONFIG,
            explicacao=(
                "Score territorial v2 calibrado para priorizar confiabilidade validada e sinal climático, "
                "preservando incidência e recência como fatores de contexto."
            ),
            ajuste_v2=True,
        )

    def _calcular_generico(
        self,
        ponto,
        *,
        clima_snapshot: dict[str, Any],
        densidade_validacoes: int,
        config: PriorizacaoConfig,
        explicacao: str,
        ajuste_v2: bool,
    ) -> PriorizacaoResultado:
        agora = timezone.now()
        dias = max((agora - ponto.criado_em).days, 0)

        score_incidencia = min(1.0, 0.4 + (densidade_validacoes * 0.05))
        score_clima = min(1.0, float(clima_snapshot.get("risco", 0.3)))
        score_confiabilidade = 1.0 if ponto.status_validacao in ("aprovado", "validado") else 0.5
        score_recencia = 1.0 if dias <= 30 else (0.7 if dias <= 180 else 0.4)

        if ajuste_v2:
            if ponto.status_validacao == "reprovado":
                score_confiabilidade = 0.2
            if dias > 365:
                score_recencia = 0.3

        score_final = (
            config.peso_incidencia * score_incidencia
            + config.peso_clima * score_clima
            + config.peso_confiabilidade * score_confiabilidade
            + config.peso_recencia * score_recencia
        )

        componentes = {
            "versao": config.versao,
            "pesos": {
                "incidencia": config.peso_incidencia,
                "clima": config.peso_clima,
                "confiabilidade": config.peso_confiabilidade,
                "recencia": config.peso_recencia,
            },
            "incidencia": round(score_incidencia, 4),
            "clima": round(score_clima, 4),
            "confiabilidade": round(score_confiabilidade, 4),
            "recencia": round(score_recencia, 4),
            "densidade_validacoes": densidade_validacoes,
            "dias_desde_observacao": dias,
        }

        return PriorizacaoResultado(
            score=round(score_final, 4),
            componentes=componentes,
            explicacao=explicacao,
        )


def calcular_score_prioridade(ponto, clima_snapshot: dict[str, Any] | None = None, densidade_validacoes: int = 0, versao: str = "v1"):
    """Facade de compatibilidade para o cálculo de priorização territorial."""

    return PriorizadorTerritorial().calcular(
        ponto,
        clima_snapshot=clima_snapshot,
        densidade_validacoes=densidade_validacoes,
        versao=versao,
    )
