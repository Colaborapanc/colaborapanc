# Contributing to ColaboraPANC

Thank you for your interest in contributing to ColaboraPANC. This document describes how to participate safely and effectively in the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How to Report Issues](#how-to-report-issues)
- [Development Workflow](#development-workflow)
- [Environment Setup](#environment-setup)
- [Running Tests](#running-tests)
- [Coding Standards](#coding-standards)
- [Pull Request Process](#pull-request-process)
- [Documentation](#documentation)
- [Scope Boundaries](#scope-boundaries)

---

## Code of Conduct

By contributing to this project, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md). Please read it before participating.

---

## How to Report Issues

- **Bugs:** Open an issue with the label `bug`, including: steps to reproduce, expected behaviour, actual behaviour, system information (OS, Python version, Django version).
- **Security vulnerabilities:** Do **not** open a public issue. Follow the procedure in [SECURITY.md](SECURITY.md).
- **Feature requests:** Open an issue with the label `enhancement`. Describe the scientific or technical justification, the affected users, and a sketch of the proposed solution.
- **Documentation gaps:** Open an issue with the label `documentation`.

---

## Development Workflow

### Branch naming

| Prefix | Purpose |
|--------|---------|
| `feat/` | New features |
| `fix/` | Bug fixes |
| `docs/` | Documentation only |
| `refactor/` | Refactoring without behaviour change |
| `test/` | Adding or fixing tests |
| `ci/` | CI/CD configuration |

### Step-by-step

1. Fork the repository and clone your fork locally.
2. Create a branch from `main` with the appropriate prefix: `git checkout -b feat/my-feature`.
3. Implement your changes with a single, focused scope (do not mix feature + refactor in one PR).
4. Write or update tests for all changed code.
5. Run the full test suite locally (see [Running Tests](#running-tests)).
6. Update documentation if any functional behaviour changed.
7. Open a Pull Request against `main` with a technical description, a summary of changes, and any risks.

---

## Environment Setup

Full instructions are available in [README.md](README.md), [docs/en/installation.md](docs/en/installation.md), and [docs/pt-BR/instalacao.md](docs/pt-BR/instalacao.md).

**Quick start (Docker recommended):**
```bash
cp .env.example .env
# Edit .env with your local values
docker compose up --build
```

**Manual setup:**
```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements_core.txt
cp .env.example .env
# Configure PostgreSQL + PostGIS (see docs installation guides)
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

---

## Running Tests

```bash
# Full suite
pytest

# With coverage report
pytest --cov=mapping --cov-report=term-missing

# Specific module
pytest tests/test_scientific_core.py -v

# Mobile (from mobile/ directory)
cd mobile && npm run test:ci
```

**Minimum expected coverage for new code:** 70 % on the changed module.

---

## Coding Standards

### Python (backend)

- Follow [PEP 8](https://peps.python.org/pep-0008/). Run `flake8 mapping/` before committing.
- Use Django ORM patterns consistently; avoid raw SQL except where justified by performance.
- Keep business logic in `services/` or `domains/`; views should delegate to services.
- New services must have at least one test in `tests/`.
- Do not store secrets, credentials, or real user data in code or fixtures.

### JavaScript (mobile)

- Follow the existing code style (ESLint configuration in `mobile/`).
- All API calls must go through `mobile/src/config/api.js` — do not hardcode URLs.
- New screens must be registered in the navigation stack in `mobile/src/navigation/`.

### Documentation

- All project documentation must be bilingual (PT-BR + EN), organized and standardized.
- Prefer one of these patterns:
  - Single file with `## Português (PT-BR)` and `## English (EN)` sections mirroring the same content.
  - Pair of files with suffixes `.pt-BR.md` and `.en.md`, linked to each other at the top.
- Keep both language versions functionally equivalent whenever documentation is updated.
- Keep a consistent structure in both languages: objective, scope, prerequisites, steps, validation, and references.
- If a functionality is only partially implemented, explicitly mark it as `[PARCIALMENTE IMPLEMENTADO]` (PT-BR) and `[PARTIALLY IMPLEMENTED]` (EN).
- For the current canonical bilingual structure, follow `docs/en/index.md` and `docs/pt-BR/index.md`.

---

## Pull Request Process

1. PRs require at least one review from a maintainer.
2. All CI checks must pass (see `.github/workflows/ci.yml`).
3. Do not merge your own PRs without review unless explicitly authorised.
4. PR description must include:
   - **What** was changed.
   - **Why** (link to issue).
   - **Risks** (data migration? API contract change? External dependency bump?).
   - **How to test** manually.
5. Keep PRs small and focused. Very large PRs will be asked to be split.

---

## Documentation

Documentation lives in `docs/`. When submitting a PR that changes behaviour:

- Update the relevant `docs/*.md` file in both PT-BR and EN according to the bilingual standard.
- If the change affects API endpoints, update `docs/en/api.md` and `docs/pt-BR/api.md`.
- If the change affects the scientific workflow, update `docs/en/modules.md` and `docs/pt-BR/modulos.md` plus any detailed legacy references when needed.

---

## Scope Boundaries

To maintain the integrity of the scientific workflow, the following areas require explicit maintainer approval before any PR is accepted:

- Changes to `mapping/models.py` (data model changes require migration strategy).
- Changes to the AI inference pipeline (`mapping/services/ia_identificacao/`).
- Changes to the human-in-the-loop validation flow (`ValidacaoEspecialista`, `HistoricoValidacao`).
- Changes to territorial prioritisation scoring (`mapping/services/priorizacao_territorial.py`).
- Any change to authentication, permissions, or CORS settings.

---

## Questions

If you are unsure about anything, open a discussion issue rather than a PR. We prefer a conversation before a large contribution.
