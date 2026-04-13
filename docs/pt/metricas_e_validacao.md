# Métricas e validação

## Endpoint fonte
`GET /api/cientifico/dashboard/`

## Métricas hoje disponíveis
- Total de pontos submetidos.
- Total de pontos com imagem.
- Total de inferências.
- Taxa de validação e rejeição.
- Concordância e divergência IA vs especialista (top-1).
- Tempo médio até validação (horas).
- Distribuição geográfica por estado.
- Top espécies sugeridas.
- Distribuição por confiança (`alta`, `media`, `baixa`).
- Amostra de priorização territorial.

## Como interpretar
- **Concordância alta** não substitui revisão humana; apenas indica proximidade IA-especialista no conjunto validado.
- **Tempo médio alto** indica gargalo de revisão.
- **Distribuição de confiança** ajuda a monitorar qualidade operacional da inferência.

## Métricas planejadas (não implementadas no código atual)
- Precisão, recall, F1 por espécie e por bioma.
- Curvas por provedor e janela temporal.
- Matriz de confusão consolidada.
