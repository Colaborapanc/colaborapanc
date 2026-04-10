# API MapBiomas (Anexo Técnico Legado)

## Status

**Reescrito e mantido como anexo técnico ativo.**
Visão canônica de integrações: `docs/pt-BR/integracoes.md`.

## Objetivo

Documentar detalhes operacionais específicos de MapBiomas além da visão de alto nível das integrações canônicas.

## Escopo coberto

- Dependências de autenticação MapBiomas (`MAPBIOMAS_EMAIL`, `MAPBIOMAS_PASSWORD`).
- Padrões de falha operacional (credencial, token, indisponibilidade externa, timeout).
- Relação com superfícies administrativas de health/teste.
- Postura de fallback esperada quando MapBiomas estiver degradado.

## Referências operacionais

- Camada de serviço: `mapping/services/mapbiomas_service.py`, `mapping/services/environment/mapbiomas.py`
- Superfície de API: `/api/mapbiomas/*`
- APIs admin de health: `/api/admin/integracoes/health/`, `/api/admin/integracoes/testar/`

## Nota de consolidação

Comportamento central fica nas docs canônicas; este anexo preserva profundidade operacional do provedor sem poluir `integracoes.md`.
