from __future__ import annotations

from typing import Iterable

MESES_PT = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]
MONTH_INDEX = {m: i + 1 for i, m in enumerate(MESES_PT)}


def _normalize_months(values: Iterable[str | int] | None) -> list[str]:
    if not values:
        return []
    out: list[str] = []
    for value in values:
        if isinstance(value, int):
            if 1 <= value <= 12:
                out.append(MESES_PT[value - 1])
            continue
        text = str(value).strip().lower()
        if text.isdigit():
            month = int(text)
            if 1 <= month <= 12:
                out.append(MESES_PT[month - 1])
                continue
        if text[:3] in MONTH_INDEX:
            out.append(text[:3])
    return list(dict.fromkeys(out))


def summarize_month_window(months: list[str]) -> str:
    if not months:
        return "nao_informado"
    unique = _normalize_months(months)
    if len(unique) == 12:
        return "ano_todo"
    if len(unique) == 1:
        return unique[0]
    ordered = sorted(unique, key=lambda m: MONTH_INDEX[m])
    return f"{ordered[0]}-{ordered[-1]}"


def calcular_colheita_periodo(
    *,
    planting_days_to_harvest: int | None,
    days_to_harvest: int | None,
    growth_months: list[str] | None,
    fruit_months: list[str] | None,
    bloom_months: list[str] | None,
) -> str | list[str]:
    """Regra explícita de consolidação agronômica para colheita.

    Prioridades:
    1) fruit_months -> meses observados de colheita direta.
    2) growth_months/bloom_months -> apoio para janela sazonal.
    3) days_to_harvest/planting_days_to_harvest -> faixas anuais aproximadas.
    """
    fruit = _normalize_months(fruit_months)
    if fruit:
        return fruit if len(fruit) <= 4 else summarize_month_window(fruit)

    growth = _normalize_months(growth_months)
    if growth:
        return growth if len(growth) <= 4 else summarize_month_window(growth)

    bloom = _normalize_months(bloom_months)
    if bloom:
        return bloom if len(bloom) <= 4 else summarize_month_window(bloom)

    days = days_to_harvest or planting_days_to_harvest
    if not days:
        return "nao_informado"

    if days <= 120:
        return "ano_todo"
    if days <= 180:
        return "set-mar"
    if days <= 270:
        return "out-mai"
    return "nao_informado"
