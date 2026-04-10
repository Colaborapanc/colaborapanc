# Legacy Technical Documentation Consolidation Matrix

## Scope

This matrix records consolidation decisions for legacy technical docs in:
- `docs/pt/*`
- legacy-equivalent files in `docs/en/*`
- other technical markdown outside canonical core when relevant.

## Destination legend

- **Active technical annex**: remains as targeted operational reference.
- **Incorporated into canonical docs**: core content absorbed by `docs/en/*` and `docs/pt-BR/*`.
- **Archived for redundancy**: retained only for historical traceability, not actively maintained.
- **Rewritten**: kept with refreshed content and explicit purpose.

## Legacy -> destination matrix

| PT legacy | EN legacy equivalent | Decision | Canonical/operational destination |
|---|---|---|---|
| `docs/pt/README.md` | `docs/en/README.md` | Rewritten | Legacy index with bridge to matrix and canonical trees |
| `docs/pt/MAPBIOMAS_API.md` | `docs/en/MAPBIOMAS_API.md` | Rewritten | **Active technical annex** for MapBiomas integration operations |
| `docs/pt/integracao_wikimedia_enriquecimento.md` | `docs/en/integracao_wikimedia_enriquecimento.md` | Rewritten | **Active technical annex** for controlled Wikimedia enrichment |
| `docs/pt/painel_integracoes_admin.md` | `docs/en/painel_integracoes_admin.md` | Rewritten | **Active technical annex** for admin integration panel operations |
| `docs/pt/troubleshooting.md` | `docs/en/troubleshooting.md` | Rewritten | **Active technical annex** for operational troubleshooting |
| `docs/pt/api_endpoints.md` | `docs/en/api_endpoints.md` | Archived for redundancy | Canonical content in `docs/pt-BR/api.md` and `docs/en/api.md` |
| `docs/pt/arquitetura_geral.md` | `docs/en/arquitetura_geral.md` | Archived for redundancy | Canonical content in `docs/pt-BR/arquitetura.md` and `docs/en/architecture.md` |
| `docs/pt/arquitetura_ia_colaborapanc.md` | `docs/en/arquitetura_ia_colaborapanc.md` | Incorporated into canonical | `docs/pt-BR/admin.md`, `docs/en/admin.md`, algorithmic-governance annexes |
| `docs/pt/configuracao_ambiente.md` | `docs/en/configuracao_ambiente.md` | Archived for redundancy | `docs/pt-BR/instalacao.md`, `docs/en/installation.md`, `.env.example` |
| `docs/pt/deploy.md` | `docs/en/deploy.md` | Archived for redundancy | `docs/pt-BR/implantacao.md`, `docs/en/deployment.md` |
| `docs/pt/documentacao_bilingue_padrao.md` | `docs/en/documentacao_bilingue_padrao.md` | Archived for redundancy | Guidance absorbed in `CONTRIBUTING.md` + canonical docs |
| `docs/pt/feature_ar_identificacao.md` | `docs/en/feature_ar_identificacao.md` | Incorporated into canonical | `docs/pt-BR/fluxos-mobile-avancados.md`, `docs/en/mobile-advanced-flows.md` |
| `docs/pt/fluxo_cientifico_do_sistema.md` | `docs/en/fluxo_cientifico_do_sistema.md` | Incorporated into canonical | `docs/pt-BR/arquitetura.md`, `docs/en/architecture.md`, modules docs |
| `docs/pt/governanca_ia.md` | `docs/en/governanca_ia.md` | Incorporated into canonical | admin algorithmic-governance annexes EN/PT-BR |
| `docs/pt/instalacao_backend.md` | `docs/en/instalacao_backend.md` | Archived for redundancy | `docs/pt-BR/instalacao.md`, `docs/en/installation.md` |
| `docs/pt/instalacao_mobile.md` | `docs/en/instalacao_mobile.md` | Archived for redundancy | `docs/pt-BR/instalacao.md`, `docs/en/installation.md` |
| `docs/pt/metricas_e_validacao.md` | `docs/en/metricas_e_validacao.md` | Incorporated into canonical | `docs/pt-BR/admin.md`, `docs/en/admin.md`, roadmap/FAQ |
| `docs/pt/mobile_arquitetura_integracao.md` | `docs/en/mobile_arquitetura_integracao.md` | Incorporated into canonical | mobile advanced annexes EN/PT-BR |
| `docs/pt/modelos_de_dados.md` | `docs/en/modelos_de_dados.md` | Archived for redundancy | canonical architecture/modules docs |
| `docs/pt/politica_dados_e_privacidade.md` | `docs/en/politica_dados_e_privacidade.md` | Incorporated into canonical | admin data/privacy annexes EN/PT-BR |
| `docs/pt/priorizacao_territorial.md` | `docs/en/priorizacao_territorial.md` | Incorporated into canonical | canonical architecture/modules/admin + roadmap |
| `docs/pt/roadmap.md` | `docs/en/roadmap.md` (legacy) | Archived for redundancy | canonical `docs/pt-BR/roadmap.md` and `docs/en/roadmap.md` |
| `docs/pt/testes.md` | `docs/en/testes.md` | Archived for redundancy | canonical installation/contributing docs + root CI policies |
| `docs/pt/trabalho_cientifico_pjc2026.md` | `docs/en/trabalho_cientifico_pjc2026.md` | Active technical annex | complementary academic/technical reference |
| `docs/pt/verificacao_detalhada_sistema_2026-04-10.md` | `docs/en/verificacao_detalhada_sistema_2026-04-10.md` | Active technical annex | point-in-time verification snapshot/historical audit |

## Final organization proposal

1. **Canonical core (active evolution):** only `docs/en/*` and `docs/pt-BR/*` tracked in canonical indexes.
2. **Legacy technical traceability:** keep `docs/pt/*` and EN extra files for historical traceability without parallel full maintenance.
3. **Allowed active legacy annexes:** only files marked as “active technical annex / rewritten” in this matrix.
4. **Update policy:** all functional updates happen first in canonical docs; legacy receives only reference notes if strictly required.
