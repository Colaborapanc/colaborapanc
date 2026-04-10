# Plano de métricas e validação científica

## Métricas implementadas no dashboard
- total de pontos submetidos
- total de pontos com imagem
- total de inferências realizadas
- taxa de validação
- taxa de rejeição
- concordância e divergência IA vs especialista
- tempo médio até validação (horas)
- distribuição geográfica
- top espécies
- distribuição por faixa de confiança
- priorização territorial (amostra)

## Métricas preparadas para evolução
- precisão, recall, F1, top-1, top-3 e matriz de confusão
- dependem de base validada suficiente e ground truth estruturado

## Estratégia de validação
- usar `ValidacaoEspecialista` como referência humana
- comparar espécie final com top-1 da IA
- manter histórico completo para auditoria e replicabilidade
