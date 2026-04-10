# Guia de Administração

## Superfícies administrativas

- Admin Django: `/admin/`
- Painel de integrações: `/painel-admin/integracoes/`
- Painel de validação: `/painel-validacao/`
- Admin de gamificação: `/gamificacao/admin/`

## Tarefas administrativas comuns

- Monitorar status de integrações e executar chamadas de teste.
- Revisar fila científica e validar/rejeitar pontos pendentes.
- Exportar CSVs de usuários e pontos.
- Executar comandos de gestão quando necessário.

## Comandos de gestão (exemplos)

- `python manage.py auditar_integracoes_funcionais`
- `python manage.py sincronizar_alertas_climaticos`
- `python manage.py sincronizar_alertas_ambientais`
- `python manage.py processar_plantas`
