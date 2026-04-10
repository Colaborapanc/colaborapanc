# Integração Wikimedia para Enriquecimento (Anexo Técnico Legado)

## Status

**Reescrito e mantido como anexo técnico ativo.**
Mapa canônico de integrações: `docs/pt-BR/integracoes.md`.

## Objetivo

Registrar comportamento orientado à implementação para enriquecimento complementar via Wikimedia em campos alimentares.

## Escopo coberto

- Modelo de uso controlado (fonte complementar, não autoridade científica única).
- Extração com consciência de confiança e fallback seguro.
- Configuração esperada e identificação responsável de cliente.
- Classes de falha (página ambígua, evidência insuficiente, baixa confiança).

## Referências operacionais

- Módulos de pipeline em `mapping/services/enrichment/*`
- Contexto complementar em docs canônicas de integrações/admin
- Leitura relacionada: `docs/pt-BR/admin.md`, `docs/pt-BR/politica-dados-privacidade-admin.md`

## Nota de consolidação

Política de alto nível permanece no canônico; este anexo preserva nuances operacionais específicas da fonte.
