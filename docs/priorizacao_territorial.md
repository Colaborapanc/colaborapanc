# Priorização territorial

## Implementação atual
Serviço: `mapping/services/priorizacao_territorial.py`.

Função principal: `calcular_score_prioridade(ponto, clima_snapshot=None, densidade_validacoes=0)`.

## Fórmula implementada
`score_final = 0.30*incidencia + 0.25*clima + 0.25*confiabilidade + 0.20*recencia`

Componentes:
- **incidência**: densidade local de validações (proxy simples).
- **clima**: risco climático recebido no snapshot (default 0.3).
- **confiabilidade**: favorece pontos já aprovados/validados.
- **recência**: observações recentes recebem peso maior.

## Saída
Objeto com:
- `score` (0 a 1),
- `componentes` (detalhamento para auditoria),
- `explicacao` textual.

## Limitações
- Heurística ainda não calibrada com séries históricas extensas.
- Dependência de snapshot climático externo quando disponível.
- Uso atual no dashboard em amostra (não pipeline batch completo).
