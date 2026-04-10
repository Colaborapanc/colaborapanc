# Painel Admin de Integrações (Anexo Técnico Legado)

## Status

**Reescrito e mantido como anexo técnico ativo.**
Operação admin canônica: `docs/pt-BR/admin.md`.

## Objetivo

Oferecer guia focado de operação do painel de saúde de integrações sem duplicar toda a governança administrativa.

## Capacidades do painel

- Status consolidado de integração (`online`, `degradada/parcial`, `offline`, `nao_configurada`).
- Diagnósticos amigáveis (`error_type`, `mensagem_amigavel`) e nível de latência.
- Ação para healthcheck completo ou reteste por integração.

## Modelo de acesso

- Painel web restrito a perfis administrativos.
- Endpoints API:
  - `GET /api/admin/integracoes/health/`
  - `POST /api/admin/integracoes/testar/`

## Uso operacional

1. Identificar integração degradada/falhando.
2. Verificar configuração/credenciais ausentes e categoria do erro.
3. Reexecutar teste e observar transição.
4. Escalonar por impacto de domínio (identificação, enriquecimento, clima/ambiental).

## Nota de consolidação

Contexto de governança/política permanece no admin canônico; este anexo segue como referência rápida de operação de UI.
