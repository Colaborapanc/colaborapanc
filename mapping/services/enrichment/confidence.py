from typing import Any


def calcular_grau_confianca_taxonomica(*, gnv_ok: bool, tropicos_ok: bool, gbif_ok: bool, inat_ok: bool, conflito_taxonomico: bool) -> float:
    score = 0.0
    if gnv_ok:
        score += 0.4
    if tropicos_ok:
        score += 0.35
    if gbif_ok:
        score += 0.15
    if inat_ok:
        score += 0.10
    if conflito_taxonomico:
        score -= 0.25
    return round(max(0.0, min(1.0, score)), 2)


def definir_status_enriquecimento(success_count: int, failure_count: int, has_scientific_name: bool) -> str:
    if not has_scientific_name:
        return "pendente"
    if success_count == 0 and failure_count > 0:
        return "falho"
    if success_count >= 4:
        return "completo"
    if success_count >= 1:
        return "parcial"
    return "pendente"
