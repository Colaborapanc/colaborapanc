# Verificação detalhada do sistema (condições atuais) / Detailed system verification (current conditions)

## Português (PT-BR)

### Escopo da revisão
Esta revisão consolida uma verificação técnica do código **no estado atual do ambiente** e uma revisão estrutural dos documentos de sistema em `docs/*.md` (raiz de `docs/`, excluindo `docs/academic/` e `docs/internal/`).

Data de referência: **2026-04-10**.

### Verificações executadas no código
1. Tentativa de instalar `requirements.txt` para execução completa.
   - Resultado: falha por dependência não disponível (`cloud-init==24.4.1`) neste ambiente de execução.
2. Tentativa de instalar `requirements_core.txt`.
   - Resultado: falha na construção de `GDAL==3.0.4` em Python 3.12 (`use_2to3 is invalid`).
3. Compilação estática Python (`compileall`) em `mapping/`, `config/`, `management/` e `tests/`.
   - Resultado: identificados arquivos com problema de codificação não UTF-8 em scripts/arquivos legados.

### Achados técnicos atuais
- **Bloqueador de ambiente**: dependências de sistema/pacotes antigos impedem setup completo com Python 3.12.
- **Débito técnico de encoding**: existem arquivos Python com caracteres Latin-1/Windows-1252 que quebram compilação UTF-8.

### Revisão dos documentos de sistema (`docs/*.md`)
Critérios aplicados por documento:
- título principal presente;
- estrutura por seções (`#`/`##`);
- ausência de placeholders (`[INSERIR]`, `TODO`, `TBD`, `FIXME`);
- coerência com o padrão bilíngue (política e checklist centralizados).

| Documento | Status | Observação |
|---|---|---|
| `docs/arquitetura_geral.md` | Revisado | Estrutura válida e objetiva. |
| `docs/arquitetura_ia_colaborapanc.md` | Revisado | Conteúdo técnico consistente. |
| `docs/fluxo_cientifico_do_sistema.md` | Revisado | Fluxo documentado e rastreável. |
| `docs/instalacao_backend.md` | Revisado | Passos de instalação claros. |
| `docs/instalacao_mobile.md` | Revisado | Fluxo mobile documentado. |
| `docs/configuracao_ambiente.md` | Revisado | Estrutura enxuta e adequada. |
| `docs/modelos_de_dados.md` | Revisado | Modelo central descrito. |
| `docs/api_endpoints.md` | Revisado | Endpoints com foco no estado real. |
| `docs/priorizacao_territorial.md` | Revisado | Heurística e critérios descritos. |
| `docs/metricas_e_validacao.md` | Revisado | Métricas e validação documentadas. |
| `docs/governanca_ia.md` | Revisado | Diretrizes de governança presentes. |
| `docs/politica_dados_e_privacidade.md` | Revisado | Política técnica descrita. |
| `docs/testes.md` | Revisado | Estratégia de testes registrada. |
| `docs/deploy.md` | Revisado | Instruções curtas e objetivas. |
| `docs/troubleshooting.md` | Revisado | Problemas comuns mapeados. |
| `docs/roadmap.md` | Revisado | Planejamento macro definido. |
| `docs/feature_ar_identificacao.md` | Revisado | Documento extenso, com cobertura funcional. |
| `docs/mobile_arquitetura_integracao.md` | Revisado | Evolução mobile detalhada. |
| `docs/integracao_wikimedia_enriquecimento.md` | Revisado | Integração descrita com escopo. |
| `docs/painel_integracoes_admin.md` | Revisado | Operação administrativa documentada. |
| `docs/MAPBIOMAS_API.md` | Revisado | Integração e endpoints detalhados. |
| `docs/PLANTAS_OFFLINE_SELETIVAS.md` | Revisado | Estratégia offline detalhada. |
| `docs/trabalho_cientifico_pjc2026.md` | **Atualizado nesta revisão** | Placeholders removidos e referências com data de acesso preenchida. |
| `docs/documentacao_bilingue_padrao.md` | Revisado | Norma bilíngue central publicada. |

### Atualizações aplicadas nesta entrega
- Atualização de `docs/trabalho_cientifico_pjc2026.md` para remover placeholders de identificação e referências pendentes.
- Inclusão deste relatório técnico para rastreabilidade da revisão de código + documentação no contexto real do ambiente.

### Próximas ações recomendadas
1. Definir baseline de runtime (ex.: Python 3.11 + versão GDAL compatível) e publicar em `docs/configuracao_ambiente.md`.
2. Corrigir encoding dos arquivos Python legados para UTF-8.
3. Executar suíte de testes completa após ajuste de dependências.

---

## English (EN)

### Review scope
This review consolidates a technical verification of the codebase **under current environment constraints** and a structural review of system documents under `docs/*.md` (root of `docs/`, excluding `docs/academic/` and `docs/internal/`).

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
- section-based structure (`#`/`##`);
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
