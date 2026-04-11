# ColaboraPANC Documentation Hub

Choose your language / Escolha seu idioma:

- 🇺🇸 **English:** [`docs/en/index.md`](./en/index.md)
- 🇧🇷 **Português (Brasil):** [`docs/pt-BR/index.md`](./pt-BR/index.md)

## Purpose of this hub

This file is the documentation entry layer. It centralizes language selection and points to the canonical documentation trees that describe the current codebase behavior.

## Canonical documentation sets

- `docs/en/`: canonical English documentation for the current product state.
- `docs/pt-BR/`: canonical Brazilian Portuguese documentation for the current product state.

Both canonical sets should keep equivalent scope and depth.

## Legacy and supporting documentation

- `docs/pt/`: legacy Portuguese documentation preserved for technical traceability and controlled migration into canonical docs.
- `docs/en/README.md`: backward-compatible legacy index for older English links.
- `docs/academic/`: paper and citation artifacts for academic dissemination.

## Coverage expected from canonical docs

The canonical indexes should route to documentation that covers:

- Backend platform architecture and operation (Django + DRF).
- API surface and endpoint families.
- Scientific workflow (AI inference, review, validation, audit trail).
- Environmental and territorial integrations (MapBiomas, climate pipeline).
- Mobile app architecture and backend parity flows.
- Auxiliary collaboration modules (notifications, conversations, gamification, routes, preferences).
- Installation, deployment, administration, contribution process, roadmap, and FAQ.

## Source-of-truth policy

When documentation conflicts exist:
1. Code is the source of truth.
2. Canonical docs (`docs/en`, `docs/pt-BR`) must be updated first.
3. Legacy docs are either migrated into canonical annexes or archived as historical records.
