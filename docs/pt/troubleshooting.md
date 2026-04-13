# Troubleshooting (Anexo Técnico Legado)

## Status

**Reescrito e mantido como anexo técnico ativo.**

## Escopo

Troubleshooting operacional rápido para problemas comuns de setup/execução que não cabem integralmente nos resumos canônicos de usuário/admin.

## Cenários comuns

### 1) Mobile não sincroniza pendências offline
- Verificar restauração de rede e URL base de API.
- Confirmar backend acessível e sessão/token válidos.
- Reexecutar sincronização e inspecionar estado da fila pendente no app.

### 2) Integração aparece offline/degradada
- Usar painel admin de integrações e endpoint de reteste.
- Verificar primeiro variáveis de ambiente/credenciais ausentes.
- Separar falha de auth/config de indisponibilidade/timeout de provedor.

### 3) Resultado de IA parece inconsistente
- Tratar saída como assistiva; verificar status de revisão.
- Confirmar se validação humana ainda está pendente.
- Revisar contexto de confiança antes de agir sobre resultado.

### 4) Divergência entre ambiente e deploy
- Revisar guias canônicos de instalação/implantação.
- Validar variáveis de ambiente e segredos.
- Confirmar configuração segura em produção (`DEBUG=False`, CORS restritivo em produção).

## Referências canônicas

- Fluxo de usuário: `docs/pt-BR/guia-do-usuario.md`
- Fluxo de contribuição: `docs/pt-BR/contribuicao.md`
- Operação administrativa: `docs/pt-BR/admin.md`
- Instalação/implantação: `docs/pt-BR/instalacao.md`, `docs/pt-BR/implantacao.md`
