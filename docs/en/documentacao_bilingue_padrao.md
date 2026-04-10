# Bilingual Documentation Standard

## Portuguese (PT-BR)

### Objective
Define a single standard for all project documentation, ensuring versions in Portuguese and English, with predictable organization and consistent maintenance.

### Mandatory rule
All new or changed documentation must exist in **PT-BR and EN**, with equivalent content in both languages.

### Accepted formats
1. **Bilingual single file (recomendado para documentos curtos/médios)**
   - Minimum structure:
     - `## Português (PT-BR)`
     - `## English (EN)`
   - Both sections must cover the same topics.

2. **File pair (recommended for long documents)**
   - Example:
     - `guia_implantacao.pt-BR.md`
     - `guia_implantacao.en.md`
   - Each file must contain, at the top, a link to the document in the other language.

### Standard content structure
Use the same structure in both languages whenever applicable:
1. Objective
2. Scope
3. Prerequisites
4. Step by step
5. Validation/Testing
6. Known limitations
7. References

### Standardization conventions
- Parallel titles and subtitles between PT-BR and EN.
- Same level of technical detail in both versions.
- When there is partial status marking, use:
  - `[PARCIALMENTE IMPLEMENTADO]` in PT-BR
  - `[PARTIALLY IMPLEMENTED]` in EN
- Avoid divergence between examples of commands, parameters and endpoints.

### Review Checklist (PR)
- [ ] The document is available in PT-BR and EN.
- [ ] The sections have semantic equivalence between languages.
- [ ] Commands and technical examples are synchronized.
- [ ] Internal links work in both versions.
- [ ] Critical terms were kept consistent (design glossary).

---

## English (EN)

###Goal
Defines a single standard for all project documentation, ensuring Portuguese and English versions with predictable organization and consistent maintenance.

### Mandatory rules
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
