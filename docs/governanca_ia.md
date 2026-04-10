# Governança de IA

## Princípios adotados
1. IA assistiva, não autônoma.
2. Revisão humana obrigatória por papel autorizado.
3. Registro auditável de decisões e divergências.
4. Transparência sobre incerteza e limites de provedores externos.

## Controles técnicos presentes
- Controle de acesso de revisão: `IsReviewerOrAdmin`.
- Persistência de predição e validação em modelos separados.
- Histórico de eventos (`HistoricoValidacao`).
- Classificação de confiança e recomendação operacional.

## Riscos conhecidos
- Viés e cobertura desigual de APIs externas por região/espécie.
- Falsos positivos em imagens de baixa qualidade.
- Dependência de disponibilidade/cotas de terceiros.

## Mitigações recomendadas
- Treinamento contínuo de revisores.
- Painéis de monitoramento de divergência por provedor.
- Registro de contexto da coleta (qualidade da imagem, órgão da planta).
