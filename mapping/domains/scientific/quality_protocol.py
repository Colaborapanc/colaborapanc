from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ResultadoQualidadePonto:
    aprovado: bool
    nivel_confianca: str
    pendencias: list[str]


def avaliar_qualidade_minima_ponto(*, latitude: float | None, longitude: float | None, nome_popular: str | None, nome_cientifico: str | None) -> ResultadoQualidadePonto:
    """Validação central mínima para preparar governança científica (fase 2).

    Não altera comportamento atual; apenas oferece utilitário reutilizável.
    """

    pendencias: list[str] = []

    if latitude is None or longitude is None:
        pendencias.append("coordenadas_ausentes")
    else:
        if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
            pendencias.append("coordenadas_invalidas")

    if not (nome_popular or nome_cientifico):
        pendencias.append("taxonomia_minima_ausente")

    if len(pendencias) >= 2:
        nivel = "baixa"
    elif len(pendencias) == 1:
        nivel = "media"
    else:
        nivel = "alta"

    return ResultadoQualidadePonto(
        aprovado=not pendencias,
        nivel_confianca=nivel,
        pendencias=pendencias,
    )
