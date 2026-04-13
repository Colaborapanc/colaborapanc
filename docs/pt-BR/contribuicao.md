# Contribuição

## Público e escopo

Este guia é para **colaboradores, mantenedores e desenvolvedores**.
Para operação de usuário final, use `docs/pt-BR/guia-do-usuario.md`.

## 1) Valores de contribuição

- Qualidade científica acima de velocidade.
- Fluxos com revisão humana acima de automação autônoma.
- Mudanças pequenas, testáveis e bem documentadas.
- Paridade documental bilíngue (EN + PT-BR).

## 2) Políticas obrigatórias do repositório

Políticas canônicas na raiz:
- [`CONTRIBUTING.md`](../../CONTRIBUTING.md)
- [`CODE_OF_CONDUCT.md`](../../CODE_OF_CONDUCT.md)
- [`SECURITY.md`](../../SECURITY.md)
- [`CHANGELOG.md`](../../CHANGELOG.md)

Este arquivo resume a camada de onboarding de colaboração dentro da documentação canônica.

## 3) Quem faz o quê

- **Colaborador:** propõe mudanças com escopo claro, testes e documentação.
- **Mantenedor:** revisa arquitetura/risco e aprova merge.
- **Operador/admin:** monitora integrações e operação científica em produção.

## 4) Checklist de onboarding para contribuição

1. Ler políticas de contribuição/segurança/código de conduta da raiz.
2. Preparar ambiente local (ver `docs/pt-BR/instalacao.md`).
3. Validar testes de baseline antes de alterar comportamento.
4. Implementar mudança focada em um domínio.
5. Atualizar docs canônicas (EN + PT-BR) sempre que houver mudança funcional.
6. Abrir PR com riscos e passos de validação manual.

## 5) Fluxo de desenvolvimento (prático)

- Usar nomenclatura de branch da política raiz (`feat/`, `fix/`, `docs/` etc.).
- Manter PRs focadas (sem misturar temas não relacionados).
- Para mudanças de comportamento, incluir testes e atualização de docs.
- Para áreas sensíveis (fluxo IA, permissões, mudança de modelo), alinhar com mantenedor cedo.

## 6) Regra de paridade documental (obrigatória)

Ao atualizar docs canônicas, espelhar conteúdo relevante em ambas as árvores:
- `docs/en/*`
- `docs/pt-BR/*`

Exige-se equivalência de escopo e densidade, não tradução literal.

## 7) Segurança e divulgação responsável

- Nunca publicar vulnerabilidades em issue pública.
- Seguir processo de divulgação descrito em `SECURITY.md`.
- Não versionar segredos, chaves ou dados sensíveis.

## 8) Barra de qualidade para contribuição

Uma contribuição é considerada pronta quando:
- o escopo está claro,
- testes/checks foram executados e reportados,
- documentação foi atualizada em EN/PT-BR,
- riscos e considerações de rollback estão explícitos.
