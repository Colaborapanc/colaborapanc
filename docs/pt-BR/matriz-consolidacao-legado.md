# Matriz de Consolidação de Documentos Legados

## Escopo

Esta matriz consolida decisões sobre documentos técnicos legados em:
- `docs/pt/*`
- arquivos equivalentes legados em `docs/en/*`
- outros `.md` técnicos fora do núcleo canônico quando aplicável.

## Legenda de destino

- **Anexo técnico ativo**: continua existindo como referência operacional específica.
- **Incorporado no canônico**: conteúdo principal absorvido por `docs/en/*` e `docs/pt-BR/*`.
- **Arquivado por redundância**: mantido apenas para rastreabilidade histórica, sem evolução ativa.
- **Reescrito**: mantido, mas com conteúdo atualizado para papel claro no ecossistema.

## Matriz legado -> destino

| Legado PT | Legado EN equivalente | Decisão | Destino canônico/operacional |
|---|---|---|---|
| `docs/pt/README.md` | `docs/en/README.md` | Reescrito | Índice legado com ponte para matriz e árvores canônicas |
| `docs/pt/MAPBIOMAS_API.md` | `docs/en/MAPBIOMAS_API.md` | Reescrito | **Anexo técnico ativo** para operação de integração MapBiomas |
| `docs/pt/integracao_wikimedia_enriquecimento.md` | `docs/en/integracao_wikimedia_enriquecimento.md` | Reescrito | **Anexo técnico ativo** do enriquecimento complementar via Wikimedia |
| `docs/pt/painel_integracoes_admin.md` | `docs/en/painel_integracoes_admin.md` | Reescrito | **Anexo técnico ativo** para operação do painel admin de integrações |
| `docs/pt/troubleshooting.md` | `docs/en/troubleshooting.md` | Reescrito | **Anexo técnico ativo** de troubleshooting operacional |
| `docs/pt/api_endpoints.md` | `docs/en/api_endpoints.md` | Arquivado por redundância | Conteúdo canônico em `docs/pt-BR/api.md` e `docs/en/api.md` |
| `docs/pt/arquitetura_geral.md` | `docs/en/arquitetura_geral.md` | Arquivado por redundância | Conteúdo canônico em `docs/pt-BR/arquitetura.md` e `docs/en/architecture.md` |
| `docs/pt/arquitetura_ia_colaborapanc.md` | `docs/en/arquitetura_ia_colaborapanc.md` | Incorporado no canônico | `docs/pt-BR/admin.md`, `docs/en/admin.md`, anexos de governança algorítmica |
| `docs/pt/configuracao_ambiente.md` | `docs/en/configuracao_ambiente.md` | Arquivado por redundância | `docs/pt-BR/instalacao.md`, `docs/en/installation.md`, `.env.example` |
| `docs/pt/deploy.md` | `docs/en/deploy.md` | Arquivado por redundância | `docs/pt-BR/implantacao.md`, `docs/en/deployment.md` |
| `docs/pt/documentacao_bilingue_padrao.md` | `docs/en/documentacao_bilingue_padrao.md` | Arquivado por redundância | Diretrizes absorvidas em `CONTRIBUTING.md` + docs canônicas |
| `docs/pt/feature_ar_identificacao.md` | `docs/en/feature_ar_identificacao.md` | Incorporado no canônico | `docs/pt-BR/fluxos-mobile-avancados.md`, `docs/en/mobile-advanced-flows.md` |
| `docs/pt/fluxo_cientifico_do_sistema.md` | `docs/en/fluxo_cientifico_do_sistema.md` | Incorporado no canônico | `docs/pt-BR/arquitetura.md`, `docs/en/architecture.md`, `modules` |
| `docs/pt/governanca_ia.md` | `docs/en/governanca_ia.md` | Incorporado no canônico | anexos admin de governança algorítmica EN/PT-BR |
| `docs/pt/instalacao_backend.md` | `docs/en/instalacao_backend.md` | Arquivado por redundância | `docs/pt-BR/instalacao.md`, `docs/en/installation.md` |
| `docs/pt/instalacao_mobile.md` | `docs/en/instalacao_mobile.md` | Arquivado por redundância | `docs/pt-BR/instalacao.md`, `docs/en/installation.md` |
| `docs/pt/metricas_e_validacao.md` | `docs/en/metricas_e_validacao.md` | Incorporado no canônico | `docs/pt-BR/admin.md`, `docs/en/admin.md`, roadmap/FAQ |
| `docs/pt/mobile_arquitetura_integracao.md` | `docs/en/mobile_arquitetura_integracao.md` | Incorporado no canônico | anexos mobile avançados EN/PT-BR |
| `docs/pt/modelos_de_dados.md` | `docs/en/modelos_de_dados.md` | Arquivado por redundância | arquitetura/módulos canônicos |
| `docs/pt/politica_dados_e_privacidade.md` | `docs/en/politica_dados_e_privacidade.md` | Incorporado no canônico | anexos admin de política de dados/privacidade EN/PT-BR |
| `docs/pt/priorizacao_territorial.md` | `docs/en/priorizacao_territorial.md` | Incorporado no canônico | arquitetura/modulos/admin + roadmap canônicos |
| `docs/pt/roadmap.md` | `docs/en/roadmap.md` (legado) | Arquivado por redundância | `docs/pt-BR/roadmap.md` e `docs/en/roadmap.md` canônicos |
| `docs/pt/testes.md` | `docs/en/testes.md` | Arquivado por redundância | instalação/contribuição canônicas + CI/política raiz |
| `docs/pt/trabalho_cientifico_pjc2026.md` | `docs/en/trabalho_cientifico_pjc2026.md` | Anexo técnico ativo | referência acadêmica/técnica complementar |
| `docs/pt/verificacao_detalhada_sistema_2026-04-10.md` | `docs/en/verificacao_detalhada_sistema_2026-04-10.md` | Anexo técnico ativo | snapshot de verificação pontual/histórico |

## Proposta final de organização

1. **Núcleo canônico (evolução ativa):** apenas `docs/en/*` e `docs/pt-BR/*` já definidos em `index.md`.
2. **Legado técnico com rastreabilidade:** manter `docs/pt/*` e extras `docs/en/*` como trilha histórica, sem duplicar manutenção contínua.
3. **Anexos ativos permitidos no legado:** apenas os listados como “anexo técnico ativo/reescrito” nesta matriz.
4. **Política de atualização:** toda mudança funcional entra primeiro no canônico; legado recebe apenas nota de referência quando estritamente necessário.
