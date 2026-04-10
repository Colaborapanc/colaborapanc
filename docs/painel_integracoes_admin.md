# Painel administrativo de integrações

## Objetivo
Permitir que perfis administrativos acompanhem saúde operacional das integrações e executem testes rápidos sem acessar logs técnicos brutos.

## Permissões
- Acesso web: usuários autenticados `is_staff` ou `is_superuser`.
- APIs:
  - `GET /api/admin/integracoes/health/`
  - `POST /api/admin/integracoes/testar/`
  - Ambas restritas a `is_staff`/`is_superuser`.

## O que a tela exibe
- Status atual (`online`, `parcial`, `offline`, `nao_configurada`, `erro_autenticacao`, `timeout`).
- Configuração/operacionalidade.
- Última verificação, último sucesso e última falha.
- Tipo resumido do problema (`error_type`).
- Indicador de latência (`baixa`, `media`, `alta`, `nao_disponivel`).
- Logs recentes simplificados por integração.

## Ações
- **Testar todas**: executa healthcheck completo.
- **Testar novamente** (por linha): executa teste apenas da integração escolhida.

## Diretrizes de UX
- UI evita stack traces e mostra `mensagem_amigavel`.
- Em execução, botões ficam desabilitados para evitar chamadas concorrentes.
- Empty state explícito quando não há integrações monitoradas.
