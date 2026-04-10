# Padrão de Documentação Bilíngue / Bilingual Documentation Standard

## Português (PT-BR)

### Objetivo
Definir um padrão único para toda documentação do projeto, garantindo versões em português e inglês, com organização previsível e manutenção consistente.

### Regra obrigatória
Toda documentação nova ou alterada deve existir em **PT-BR e EN**, com conteúdo equivalente em ambos os idiomas.

### Formatos aceitos
1. **Arquivo único bilíngue (recomendado para documentos curtos/médios)**
   - Estrutura mínima:
     - `## Português (PT-BR)`
     - `## English (EN)`
   - As duas seções devem cobrir os mesmos tópicos.

2. **Par de arquivos (recomendado para documentos longos)**
   - Exemplo:
     - `guia_implantacao.pt-BR.md`
     - `guia_implantacao.en.md`
   - Cada arquivo deve conter, no topo, link para o documento no outro idioma.

### Estrutura padrão de conteúdo
Use a mesma estrutura nos dois idiomas sempre que aplicável:
1. Objetivo
2. Escopo
3. Pré-requisitos
4. Passo a passo
5. Validação/Testes
6. Limitações conhecidas
7. Referências

### Convenções de padronização
- Títulos e subtítulos paralelos entre PT-BR e EN.
- Mesmo nível de detalhamento técnico nas duas versões.
- Quando houver marcação de status parcial, use:
  - `[PARCIALMENTE IMPLEMENTADO]` em PT-BR
  - `[PARTIALLY IMPLEMENTED]` em EN
- Evite divergência entre exemplos de comandos, parâmetros e endpoints.

### Checklist de revisão (PR)
- [ ] O documento está disponível em PT-BR e EN.
- [ ] As seções possuem equivalência semântica entre idiomas.
- [ ] Comandos e exemplos técnicos estão sincronizados.
- [ ] Links internos funcionam nas duas versões.
- [ ] Termos críticos foram mantidos consistentes (glossário de projeto).

---

## English (EN)

### Goal
Define a single standard for all project documentation, ensuring Portuguese and English versions with predictable organization and consistent maintenance.

### Mandatory rule
All new or updated documentation must exist in **PT-BR and EN**, with equivalent content in both languages.

### Accepted formats
1. **Single bilingual file (recommended for short/medium documents)**
   - Minimum structure:
     - `## Português (PT-BR)`
     - `## English (EN)`
   - Both sections must cover the same topics.

2. **File pair (recommended for long documents)**
   - Example:
     - `deployment_guide.pt-BR.md`
     - `deployment_guide.en.md`
   - Each file must include, at the top, a link to the other language version.

### Standard content structure
Use the same structure in both languages whenever applicable:
1. Goal
2. Scope
3. Prerequisites
4. Step-by-step
5. Validation/Tests
6. Known limitations
7. References

### Standardization conventions
- Parallel headings/subheadings between PT-BR and EN.
- Same technical depth in both versions.
- When partial implementation status is needed, use:
  - `[PARCIALMENTE IMPLEMENTADO]` in PT-BR
  - `[PARTIALLY IMPLEMENTED]` in EN
- Avoid divergence in command examples, parameters, and endpoints.

### PR review checklist
- [ ] The document is available in PT-BR and EN.
- [ ] Sections are semantically equivalent across languages.
- [ ] Commands and technical examples are synchronized.
- [ ] Internal links work in both versions.
- [ ] Critical terms remain consistent (project glossary).
