# Integrations Admin Panel (Legacy Technical Annex)

## Status

**Rewritten and maintained as active technical annex.**
Canonical admin operation: `docs/en/admin.md`.

## Purpose

Provide focused operator guidance for integration-health panel behavior without duplicating full admin governance docs.

## Panel capabilities

- Consolidated integration status (`online`, `degradada/parcial`, `offline`, `nao_configurada`).
- Friendly diagnostics (`error_type`, `mensagem_amigavel`) and response latency levels.
- Trigger full healthcheck or per-integration retest actions.

## Access model

- Web panel restricted to administrative profiles.
- API endpoints:
  - `GET /api/admin/integracoes/health/`
  - `POST /api/admin/integracoes/testar/`

## Operational usage

1. Identify failing/degraded integration.
2. Check missing configuration/credentials and error category.
3. Re-test and observe transition.
4. Escalate by domain impact (identification, enrichment, climate/environment).

## Consolidation note

Governance/policy context stays in canonical admin docs; this annex stays as UI-operation quick reference.
