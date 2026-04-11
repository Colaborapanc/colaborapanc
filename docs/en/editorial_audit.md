# Editorial Audit for SoftwareX Alignment (Baseline)

Date: 2026-04-11
Scope: Local repository contents only (no external publication assumptions).

## 1. Repository snapshot

ColaboraPANC already contains:

- Active software code for backend (`config/`, `mapping/`), tests (`tests/`), and mobile client (`mobile/`).
- Bilingual documentation hubs and canonical trees (`docs/en/`, `docs/pt-BR/`).
- Academic artifacts under `docs/academic/` (`CITATION.cff`, `codemeta.json`, `paper.md`, `paper.bib`).
- Governance and community files (`CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`).

## 2. Files relevant to SoftwareX readiness

Located in repository (as of this audit):

- Root README files: `README.md`, `README.pt-BR.md`.
- Documentation hubs: `docs/README.md`, `docs/en/index.md`, `docs/pt-BR/index.md`.
- License file: `LICENSE`.
- Changelog: `CHANGELOG.md`.
- Metadata currently outside root: `docs/academic/CITATION.cff`, `docs/academic/codemeta.json`.
- Manuscript draft source: `docs/academic/paper.md`.
- Environment template: `.env.example`.
- Tests: `tests/` plus `mapping/tests.py`.

## 3. Initial gaps vs. a typical SoftwareX submission package

1. **Metadata location gap**: citation and codemeta are not in repository root.
2. **README scope gap**: root README is strong technically, but still needs explicit SoftwareX-style sections (reproducibility, citation status, archival/release status).
3. **Editorial package gap**: no dedicated local `submission/softwarex/` scaffold yet.
4. **Reproducibility/data statement gap**: data/demo expectations are not consolidated in a dedicated data statement structure.
5. **Testing discoverability gap**: tests exist, but need a concise evaluator-focused testing guide.
6. **Release workflow gap**: changelog exists, but release preparation tasks for DOI/archive are not captured in one checklist.

## 4. Risk and constraints log (for conservative execution)

- No destructive moves of source code should be performed unless clearly safe.
- No fabricated DOI, ORCID, publication status, or external deposits.
- Any external/publication-dependent action must be marked as pending author action.

## 5. Next-step baseline

This audit serves as the baseline for staged commits to improve:

- Documentation clarity and bilingual indexing.
- Metadata normalization for publication readiness.
- Reproducibility/testing guidance.
- SoftwareX editorial submission scaffolding.
