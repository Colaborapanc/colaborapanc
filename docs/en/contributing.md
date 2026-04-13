# Contributing

## Audience and scope

This guide is for **contributors, maintainers, and developers**.
For end-user operation, use `docs/en/user-guide.md`.

## 1) Contribution values

- Scientific quality over speed.
- Human-reviewed workflows over autonomous automation.
- Small, testable, and well-documented changes.
- Bilingual documentation parity (EN + PT-BR).

## 2) Required repository policies

Canonical policies at repository root:
- [`CONTRIBUTING.md`](../../CONTRIBUTING.md)
- [`CODE_OF_CONDUCT.md`](../../CODE_OF_CONDUCT.md)
- [`SECURITY.md`](../../SECURITY.md)
- [`CHANGELOG.md`](../../CHANGELOG.md)

This file summarizes the contributor onboarding layer in canonical docs.

## 3) Who does what

- **Contributor:** proposes scoped changes with tests/docs.
- **Maintainer:** reviews architecture/risk and approves merges.
- **Operator/admin:** monitors integrations and scientific operations in production.

## 4) Onboarding checklist for contributors

1. Read root contribution/security/code-of-conduct policies.
2. Set up local environment (see `docs/en/installation.md`).
3. Validate baseline tests before changing behavior.
4. Implement focused change in one domain.
5. Update canonical docs (EN + PT-BR) whenever behavior changes.
6. Submit PR with risk notes and manual validation steps.

## 5) Development workflow (practical)

- Use branch naming from root policy (`feat/`, `fix/`, `docs/`, etc.).
- Keep PRs focused (avoid mixing unrelated concerns).
- For behavior changes, include tests and docs updates.
- For sensitive areas (AI flow, permissions, model changes), request maintainer alignment early.

## 6) Documentation parity rule (mandatory)

When updating canonical docs, mirror relevant content in both trees:
- `docs/en/*`
- `docs/pt-BR/*`

Equivalent scope and density are required, not literal translation.

## 7) Security and responsible disclosure

- Never publish vulnerabilities in public issues.
- Follow `SECURITY.md` disclosure process.
- Do not commit secrets, keys, or sensitive data.

## 8) Contribution quality bar

A contribution is considered ready when:
- scope is clear,
- tests/checks are run and reported,
- docs are updated in EN/PT-BR,
- risks and rollback considerations are explicit.
