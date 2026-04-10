# Anexo Administrativo: Governança Algorítmica

## Escopo

Este anexo define controles de governança algorítmica para operação administrativa e de revisão.

## 1) Princípios centrais
1. IA assistiva, não autoridade científica autônoma.
2. Validação humana obrigatória para decisão científica final.
3. Auditabilidade de predição, revisão e justificativa de divergência.
4. Transparência operacional sobre incerteza e limites de provedores.

## 2) Controles de governança em operação
- Fronteiras de permissão revisor/admin nos endpoints científicos.
- Persistência separada para artefatos de predição IA e validação humana.
- Rastreamento histórico de eventos de transição do ciclo.
- Interpretação operacional com base em confiança/risco.

## 3) Fluxo de supervisão de governança
1. Confirmar contexto de qualidade da inferência (imagem, metadados, resposta de provedor).
2. Validar trilha de decisão do revisor e justificativa de divergência quando aplicável.
3. Acompanhar tendência de concordância/divergência ao longo do tempo.
4. Escalonar deriva de provedor ou regressões de qualidade para operação.

## 4) Riscos algorítmicos conhecidos
- Viés de cobertura por região/espécie em provedores externos.
- Falsos positivos por baixa qualidade de imagem.
- Indisponibilidade, limites de quota ou deriva comportamental de provedores.
- Risco de uso indevido quando saída assistiva é tratada como verdade final.

## 5) Base de mitigação
- Calibração contínua de revisores e critérios de decisão.
- Monitoramento por faixa de confiança e padrão de divergência.
- Tratamento estruturado de incidentes de instabilidade de provedor.
- Preservar governança de “humano decide” em runbooks operacionais.
