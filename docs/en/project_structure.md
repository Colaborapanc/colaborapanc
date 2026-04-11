# Project Structure Map

Date: 2026-04-11

This map summarizes the current repository organization for technical and editorial review.

## Top-level overview

- `config/` — Django project configuration (settings, URLs, ASGI/WSGI, context processors).
- `mapping/` — main application domain (models, views, services, serializers, migrations, admin, utilities).
- `tests/` — pytest-based backend/domain integration tests.
- `mobile/` — Expo/React Native mobile application.
- `docs/` — multilingual and academic documentation.
- `scripts/` — operational setup scripts.
- `static/`, `templates/`, `photos/` — static assets, templates, and media placeholders.

## Documentation tree

- `docs/README.md` — language/documentation hub.
- `docs/en/` — canonical English documentation set.
- `docs/pt-BR/` — canonical Brazilian Portuguese documentation set.
- `docs/pt/` — legacy Portuguese documentation preserved for traceability.
- `docs/academic/` — manuscript and software metadata artifacts.

## Metadata and governance files

- `LICENSE`
- `CHANGELOG.md`
- `.env.example`
- `CONTRIBUTING.md`
- `CODE_OF_CONDUCT.md`
- `SECURITY.md`

## SoftwareX-oriented structural observations

- Core software code is present and testable.
- Documentation is broad and bilingual, requiring final editorial harmonization.
- Metadata files exist but need root-level normalization for discoverability.
- A dedicated submission package directory is not yet present and should be added.
