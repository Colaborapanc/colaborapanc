# Testing and Validation Pathways

## Purpose

This guide provides evaluator-oriented instructions to validate ColaboraPANC locally without changing production infrastructure.

## Test locations

- Main automated tests: `tests/`
- Additional module-level tests: `mapping/tests.py`

## Recommended baseline command

```bash
python manage.py test tests
```

## Alternative command (pytest-style)

```bash
pytest tests
```

## Suggested validation sequence

1. Install dependencies from `requirements_core.txt`.
2. Configure `.env` from `.env.example`.
3. Ensure PostgreSQL/PostGIS and migrations are available.
4. Run backend tests.
5. Start server and manually verify `/healthz/`.

## Notes for reviewers

- Some service paths rely on external providers and may require credentials to fully exercise integration branches.
- The automated suite in `tests/` is the primary non-interactive validation path for core logic.
