# FAQ

## Audience note

This FAQ is written for **end users and contributors**. For deep admin operations, see `docs/en/admin.md`.

## 1) Is ColaboraPANC only a web app?
No. The platform includes a Django web/API backend and an Expo/React Native mobile app.

## 2) Is species validation fully automated by AI?
No. AI is assistive. Final scientific validation is performed by authorized human reviewers.

## 3) Why was my point not immediately “validated”?
Because points can pass through review queue and quality checks before final validation.

## 4) Can I use the app without internet?
Yes, for supported offline flows. Records can be queued locally and synchronized later.

## 5) What if AI suggestion disagrees with human review?
Human-reviewed decision is authoritative; divergence is part of traceable quality governance.

## 6) Where can I check API routes and endpoint groups?
`mapping/urls.py` is source of truth. Canonical grouped docs: `docs/en/api.md`.

## 7) Who can access admin integration operations?
Administrative profiles (`is_staff`/`is_superuser`) can access integration panel and test endpoints.

## 8) How is privacy handled in operational practice?
Platform follows technical privacy/data governance guidelines (purpose, minimization, access control, retention by policy).
See: `docs/en/admin-data-privacy-policy.md`.

## 9) Are all integrations always online?
No. External providers can be degraded/offline. Admin health/test endpoints exist for operational monitoring.

## 10) Where should contributors start?
Read root policies (`CONTRIBUTING.md`, `SECURITY.md`, `CODE_OF_CONDUCT.md`) and then `docs/en/contributing.md`.

## 11) Which docs are canonical vs legacy?
Canonical sets are `docs/en/` and `docs/pt-BR/`. Legacy/support docs remain for historical traceability.

## 12) Where do I report vulnerabilities?
Do not open a public issue. Follow `SECURITY.md` responsible disclosure process.
