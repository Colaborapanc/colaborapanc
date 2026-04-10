# Detailed system verification (current conditions)

## Portuguese (PT-BR)

### Scope of review
This review consolidates a technical check of the code **in the current state of the environment** and a structural review of the system documents in `docs/*.md` (root of `docs/`, excluding `docs/academic/` and `docs/internal/`).

Reference date: **2026-04-10**.

### Checks performed on the code
1. Attempt to install `requirements.txt` for full execution.
- Result: failure due to unavailable dependency (`cloud-init==24.4.1`) in this execution environment.
2. Attempt to install `requirements_core.txt`.
- Result: `GDAL==3.0.4` construction failed in Python 3.12 (`use_2to3 is invalid`).
3. Python static compilation (`compileall`) into `mapping/`, `config/`, `management/` and `tests/`.
- Result: identified files with non-UTF-8 encoding problem in legacy scripts/files.

### Current technical findings
- **Environment blocker**: system dependencies/old packages prevent complete setup with Python 3.12.
- **Encoding technical debt**: there are Python files with Latin-1/Windows-1252 characters that break UTF-8 compilation.

### Review of system documents (`docs/*.md`)
Criteria applied per document:
- main title present;
- structure by (__CODE0__/__CODE1__) sections;
- absence of placeholders (`[INSERIR]`, `TODO`, `TBD`, `FIXME`);
- coherence with the bilingual standard (centralized policy and checklist).

| Document | Status | Note |
|---|---|---|
| `docs/arquitetura_geral.md` | Revised | Valid and objective structure. |
| `docs/arquitetura_ia_colaborapanc.md` | Revised | Consistent technical content. |
| `docs/fluxo_cientifico_do_sistema.md` | Revised | Documented and traceable flow. |
| `docs/instalacao_backend.md` | Revised | Clear installation steps. |
| `docs/instalacao_mobile.md` | Revised | Documented mobile flow. |
| `docs/configuracao_ambiente.md` | Revised | Lean and adequate structure. |
| `docs/modelos_de_dados.md` | Revised | Central model described. |
| `docs/api_endpoints.md` | Revised | Endpoints focused on the real state. |
| `docs/priorizacao_territorial.md` | Revised | Heuristics and criteria described. |
| `docs/metricas_e_validacao.md` | Revised | Documented metrics and validation. |
| `docs/governanca_ia.md` | Revised | Present governance guidelines. |
| `docs/politica_dados_e_privacidade.md` | Revised | Technical policy described. |
| `docs/testes.md` | Revised | Registered testing strategy. |
| `docs/deploy.md` | Revised | Short and objective instructions. |
| `docs/troubleshooting.md` | Revised | Common problems mapped. |
| `docs/roadmap.md` | Revised | Defined macro planning. |
| `docs/feature_ar_identificacao.md` | Revised | Extensive document, with functional coverage. |
| `docs/mobile_arquitetura_integracao.md` | Revised | Detailed mobile evolution. |
| `docs/integracao_wikimedia_enriquecimento.md` | Revised | Integration described with scope. |
| `docs/painel_integracoes_admin.md` | Revised | Documented administrative operation. |
| `docs/MAPBIOMAS_API.md` | Revised | Detailed integration and endpoints. |
| `docs/PLANTAS_OFFLINE_SELETIVAS.md` | Revised | Detailed offline strategy. |
| `docs/trabalho_cientifico_pjc2026.md` | **Updated in this review** | Placeholders removed and references with access date filled in. |
| `docs/documentacao_bilingue_padrao.md` | Revised | Central bilingual standard published. |

### Updates applied to this delivery
- Updated `docs/trabalho_cientifico_pjc2026.md` to remove identifying placeholders and dangling references.
- Inclusion of this technical report for traceability of code review + documentation in the real context of the environment.

### Recommended next actions
1. Define runtime baseline (e.g.: Python 3.11 + compatible GDAL version) and publish to `docs/configuracao_ambiente.md`.
2. Correct encoding of legacy Python files to UTF-8.
3. Run complete test suite after adjusting dependencies.

---

## English (EN)

### Review scope
This review consolidates a technical verification of the codebase **under current environmental constraints** and a structural review of system documents under `docs/*.md` (root of `docs/`, excluding `docs/academic/` and `docs/internal/`).

Reference date: **2026-04-10**.

### Code checks executed
1. Attempted full installation via `requirements.txt`.
- Result: failed due to unavailable dependency (`cloud-init==24.4.1`) in this execution environment.
2. Attempted installation via `requirements_core.txt`.
- Result: failed while building `GDAL==3.0.4` on Python 3.12 (`use_2to3 is invalid`).
3. Static Python compilation (`compileall`) on `mapping/`, `config/`, `management/`, and `tests/`.
- Result: identified legacy files with non-UTF-8 encoding issues.

### Current technical findings
- **Environment blocker**: legacy/system dependencies prevent full setup on Python 3.12.
- **Encoding technical debt**: some Python files still contain Latin-1/Windows-1252 characters that break UTF-8 compilation.

### System documents review (`docs/*.md`)
Applied criteria per document:
- top-level title present;
- section-based structure (__CODE0__/__CODE1__);
- no unresolved placeholders (`[INSERIR]`, `TODO`, `TBD`, `FIXME`);
- coherence with the bilingual standard (policy + centralized checklist).

All listed root-level system docs were reviewed structurally. `docs/trabalho_cientifico_pjc2026.md` was updated in this delivery to remove unresolved placeholders and fill reference access dates.

### Updates included in this delivery
- Updated `docs/trabalho_cientifico_pjc2026.md` to remove identification/reference placeholders.
- Added this technical report for traceability of code + documentation review under current runtime constraints.

### Recommended next actions
1. Define runtime baseline (e.g., Python 3.11 + compatible GDAL) and publish it in `docs/configuracao_ambiente.md`.
2. Convert legacy Python files to UTF-8.
3. Run the full test suite after dependency alignment.
