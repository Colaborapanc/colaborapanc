# Admin Guide

## Scope and separation of responsibilities

This canonical guide covers **administrative and operational usage** of ColaboraPANC.

To keep governance concerns clear and auditable, this documentation is explicitly split into 3 layers:

1. **Administrative operation (this file):** roles, permissions, curation/review, integrations operations, observability, scientific-flow supervision.
2. **Algorithmic governance:** principles, controls, risks, and mitigation for assistive AI.
3. **Data/privacy policy:** data classes, minimization, retention, access control, and privacy safeguards.

### Canonical companion annexes
- Algorithmic governance annex: [`admin-algorithmic-governance.md`](./admin-algorithmic-governance.md)
- Data/privacy annex: [`admin-data-privacy-policy.md`](./admin-data-privacy-policy.md)

## 1) Administrative surfaces

- Django admin: `/admin/`
- Integrations panel: `/painel-admin/integracoes/`
- Validation panel: `/painel-validacao/`
- Gamification admin: `/gamificacao/admin/`
- Admin integration APIs:
  - `GET /api/admin/integracoes/health/`
  - `POST /api/admin/integracoes/testar/`

## 2) Roles and permissions

## 2.1 Administrative profiles
- **`is_staff` / `is_superuser`:** access to admin panels and integration operation APIs.
- **Reviewer/Admin permissions:** scientific review actions are protected by reviewer/admin controls (e.g., reviewer role checks and `IsReviewerOrAdmin` in scientific endpoints).

## 2.2 Operational permission boundaries
- Integration operation (health/test) is admin-only.
- Scientific validation actions are restricted to authorized reviewer/admin roles.
- Sensitive exports and operational commands must be run only by trusted operators.

## 3) Curation and human review operations

## 3.1 Scientific curation lifecycle (admin perspective)
1. Inspect pending points and queue state.
2. Review image/inference evidence.
3. Approve/reject/request further review.
4. Register divergence rationale when AI and human conclusions differ.
5. Confirm traceability artifacts were persisted.

## 3.2 Governance rule
- AI outputs are **assistive only**.
- Final scientific decision is **human-reviewed** and must remain auditable.

## 4) Integrations operations

## 4.1 Integration panel responsibilities
- Monitor health (`online`, `degradada/parcial`, `offline`, `nao_configurada`).
- Trigger full or per-integration test probes.
- Inspect friendly diagnostics (`mensagem_amigavel`, `error_type`), last success/failure, and latency level.

## 4.2 Typical operational triage
1. Check status and missing env vars.
2. Distinguish credential/config failure vs network/provider outage.
3. Re-test the affected integration.
4. Apply fallback-aware incident handling by domain (identification, enrichment, climate/environment).
5. Record incident context and resolution actions.

## 5) Scientific-flow supervision

## 5.1 Oversight checkpoints
- Inference generation status.
- Queue throughput and pending volume.
- Validation outcomes (`validado`, `rejeitado`, `necessita_revisao`).
- Human/AI divergence signals.
- Enrichment status and partial-failure behavior.

## 5.2 Supervisory metrics (operational)
- Validation/rejection rates.
- Agreement/divergence trend.
- Average time to validation.
- Confidence-band distribution.

## 6) Observability and traceability

## 6.1 Operational observability
- Use integration panel and admin endpoints as first operational signal.
- Track latency and status transitions over time.
- Keep troubleshooting focused on domain impact.

## 6.2 Traceability requirements
- Preserve scientific history events and validation records.
- Preserve integration test outcomes and last-failure metadata.
- Keep reviewer decisions, divergence rationale, and decision chronology auditable.

## 7) Operational command baseline (examples)

- `python manage.py auditar_integracoes_funcionais`
- `python manage.py sincronizar_alertas_climaticos`
- `python manage.py sincronizar_alertas_ambientais`
- `python manage.py processar_plantas`

Use management commands as controlled operational procedures, with role-restricted execution and audit logging.

## 8) What belongs outside this file

To avoid mixing concerns:
- AI governance specifics (principles/risks/mitigations) belong to [`admin-algorithmic-governance.md`](./admin-algorithmic-governance.md).
- Data and privacy policy specifics (LGPD-aligned technical policy) belong to [`admin-data-privacy-policy.md`](./admin-data-privacy-policy.md).
