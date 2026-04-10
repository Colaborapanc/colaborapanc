# ColaboraPANC Documentation (English)

> Language switch: [English](./index.md) | [Português (Brasil)](../pt-BR/index.md)

This is the canonical English documentation tree for the current ColaboraPANC codebase.

## Core navigation

- [Installation](./installation.md)
- [Deployment](./deployment.md)
- [Architecture](./architecture.md)
- [API](./api.md)
- [Integrations](./integrations.md)
- [Modules](./modules.md)
- [Admin](./admin.md)
- [Admin: Algorithmic Governance Annex](./admin-algorithmic-governance.md)
- [Admin: Data & Privacy Annex](./admin-data-privacy-policy.md)
- [User Guide](./user-guide.md)
- [Contributing](./contributing.md)
- [Roadmap](./roadmap.md)
- [FAQ](./faq.md)
- [Mobile Advanced Flows (Technical Annex)](./mobile-advanced-flows.md)

## What these docs represent

This canonical set reflects active system behavior implemented in the repository, including:

- Django + DRF backend routes and web/API composition.
- Scientific flow endpoints for AI inference, review queue, validation, and decision history.
- Environmental/territorial capabilities (MapBiomas and climate alert pipeline).
- Mobile parity APIs and Expo/React Native mobile client integration.
- Auxiliary collaboration modules (notifications, conversations, gamification, routes, preferences).
- Current test and operation baseline.

## Source references used to keep this index grounded

- URL and endpoint registry: `mapping/urls.py`, `config/urls.py`.
- Services and domain modules: `mapping/services/`, `mapping/domains/`, `mapping/views*.py`, `mapping/models.py`.
- Mobile app scripts/dependencies: `mobile/package.json`, `mobile/src/*`.
- Test suite: `tests/*.py`.

## Related entry points

- Documentation hub: [`docs/README.md`](../README.md)
- Root project README (EN): [`README.md`](../../README.md)
- Root project README (PT-BR): [`README.pt-BR.md`](../../README.pt-BR.md)
- Legacy Portuguese index: [`docs/pt/README.md`](../pt/README.md)
- Legacy English index: [`docs/en/README.md`](./README.md)
