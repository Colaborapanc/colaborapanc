# Documentation Audit and Reorganization Report (2026-04-10)

## Stage 1 — Documentary Audit

### 1.1 Files found before restructuring (`*.md`)

| File | Classification | Reason |
|---|---|---|
| `README.md` | partially outdated | Was bilingual in a single file and pointed to old Portuguese tree (`docs/pt/`). |
| `CONTRIBUTING.md` | updated | Contributor policy is coherent and generic. |
| `SECURITY.md` | updated | Security policy still valid. |
| `CHANGELOG.md` | updated | Historical log document. |
| `CODE_OF_CONDUCT.md` | updated | Generic policy, still valid. |
| `static/img/README.md` | updated | Asset-folder local note. |
| `docs/README.md` | partially outdated | Did not point to `docs/pt-BR/` canonical structure. |
| `docs/internal/plano_metricas_e_validacao.md` | partially outdated | Planning artifact with limited operational context. |
| `docs/academic/paper.md` | updated | Academic artifact, not operational docs. |
| `docs/pt/README.md` | partially outdated | Index tied to legacy structure. |
| `docs/en/README.md` | partially outdated | Index tied to legacy structure and mixed filename conventions. |
| `docs/pt/arquitetura_geral.md` + `docs/en/arquitetura_geral.md` | updated | Still technically aligned with current backend/mobile architecture. |
| `docs/pt/arquitetura_ia_colaborapanc.md` + `docs/en/arquitetura_ia_colaborapanc.md` | partially outdated | Valid concepts, but not aligned with new canonical navigation model. |
| `docs/pt/mobile_arquitetura_integracao.md` + `docs/en/mobile_arquitetura_integracao.md` | partially outdated | Deep details valid, but naming/navigation inconsistent for current docs standard. |
| `docs/pt/feature_ar_identificacao.md` + `docs/en/feature_ar_identificacao.md` | partially outdated | Feature scope valid, but document structure not standardized. |
| `docs/pt/api_endpoints.md` + `docs/en/api_endpoints.md` | partially outdated | Route grouping needed normalization and new canonical `api.md`. |
| `docs/pt/modelos_de_dados.md` + `docs/en/modelos_de_dados.md` | updated | Domain references remain useful and real. |
| `docs/pt/integracao_wikimedia_enriquecimento.md` + `docs/en/integracao_wikimedia_enriquecimento.md` | updated | Integration still present in service layer. |
| `docs/pt/MAPBIOMAS_API.md` + `docs/en/MAPBIOMAS_API.md` | updated | Integration present and tested. |
| `docs/pt/PLANTAS_OFFLINE_SELETIVAS.md` + `docs/en/PLANTAS_OFFLINE_SELETIVAS.md` | partially outdated | Functionality exists but required alignment with mobile parity docs. |
| `docs/pt/governanca_ia.md` + `docs/en/governanca_ia.md` | updated | Governance principles still coherent. |
| `docs/pt/politica_dados_e_privacidade.md` + `docs/en/politica_dados_e_privacidade.md` | updated | Policy remains relevant. |
| `docs/pt/metricas_e_validacao.md` + `docs/en/metricas_e_validacao.md` | partially outdated | Metrics endpoint valid; needed better linkage to scientific flow docs. |
| `docs/pt/fluxo_cientifico_do_sistema.md` + `docs/en/fluxo_cientifico_do_sistema.md` | updated | Core scientific workflow still current. |
| `docs/pt/priorizacao_territorial.md` + `docs/en/priorizacao_territorial.md` | updated | Service exists and tests cover domain logic. |
| `docs/pt/painel_integracoes_admin.md` + `docs/en/painel_integracoes_admin.md` | updated | Admin endpoints and panel exist. |
| `docs/pt/configuracao_ambiente.md` + `docs/en/configuracao_ambiente.md` | updated | Env variable baseline still relevant. |
| `docs/pt/instalacao_backend.md` + `docs/en/instalacao_backend.md` | partially outdated | Needed canonical installation entrypoint and language-tree parity. |
| `docs/pt/instalacao_mobile.md` + `docs/en/instalacao_mobile.md` | partially outdated | Needed canonical installation entrypoint and language-tree parity. |
| `docs/pt/deploy.md` + `docs/en/deploy.md` | partially outdated | Needed deployment checklist standardization. |
| `docs/pt/testes.md` + `docs/en/testes.md` | partially outdated | Test list valid but not linked to current bilingual structure. |
| `docs/pt/troubleshooting.md` + `docs/en/troubleshooting.md` | updated | Practical troubleshooting remained useful. |
| `docs/pt/roadmap.md` + `docs/en/roadmap.md` | partially outdated | Needed refresh for current priorities and language tree parity. |
| `docs/pt/documentacao_bilingue_padrao.md` + `docs/en/documentacao_bilingue_padrao.md` | redundant | Superseded by implemented canonical structure and this audit record. |
| `docs/pt/trabalho_cientifico_pjc2026.md` + `docs/en/trabalho_cientifico_pjc2026.md` | updated | Research-facing content, external to operational docs. |
| `docs/pt/verificacao_detalhada_sistema_2026-04-10.md` + `docs/en/verificacao_detalhada_sistema_2026-04-10.md` | updated | Valuable verification snapshot, retained as historical baseline. |

### 1.2 Missing-but-necessary docs (before this refactor)

- Canonical bilingual index with mirrored navigation (`docs/en/index.md`, `docs/pt-BR/index.md`).
- Canonical short-form docs with predictable names (`installation`, `deployment`, `architecture`, `api`, etc.) mirrored by language.
- Root-level Portuguese README (`README.pt-BR.md`).
- Explicit language-switch block at top of both README files.

## Stage 2 — Reorganization Proposal and Execution

### 2.1 Final documentation tree (canonical)

```text
colaborapanc/
  README.md
  README.pt-BR.md
  docs/
    README.md
    en/
      index.md
      installation.md
      deployment.md
      architecture.md
      api.md
      integrations.md
      modules.md
      admin.md
      user-guide.md
      contributing.md
      roadmap.md
      faq.md
    pt-BR/
      index.md
      instalacao.md
      implantacao.md
      arquitetura.md
      api.md
      integracoes.md
      modulos.md
      admin.md
      guia-do-usuario.md
      contribuicao.md
      roadmap.md
      faq.md
```

### 2.2 File treatment map

- **Maintained**: root governance files (`CONTRIBUTING.md`, `SECURITY.md`, `CHANGELOG.md`, `CODE_OF_CONDUCT.md`) and technical deep-dive legacy docs.
- **Rewritten**: `README.md`, `docs/README.md`, `docs/en/README.md`, `docs/pt/README.md`.
- **Created from scratch**: all canonical files in `docs/en/` and `docs/pt-BR/` listed in section 2.1 + `README.pt-BR.md`.
- **Consolidated logically**: installation/deployment/architecture/API/admin/user guidance now centralized in canonical short-form docs.
- **Archived by retention (no destructive removal)**: legacy detailed docs kept in place (`docs/pt/`, legacy-named files inside `docs/en/`) for traceability and backward links.

## Stage 5 — Final Verification

### 5.1 Validation checklist

- Bilingual README split completed (`README.md` in EN + `README.pt-BR.md` in PT-BR).
- Language switch links present at top of both READMEs.
- Canonical docs in mirrored directory trees with equivalent scope.
- Internal navigation links updated to point to language-specific trees.
- Legacy docs explicitly marked as historical/compatibility sources.

### 5.2 Manual confirmation still recommended

- Validate every legacy deep-dive file for endpoint-level drift against `mapping/urls.py` after future API changes.
- Decide long-term archival policy for old `docs/pt/` and legacy-named files in `docs/en/`.
- Optionally automate markdown link checking in CI to detect future broken references.
