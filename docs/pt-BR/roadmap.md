# Roadmap

## Escopo e modelo de honestidade

Este roadmap separa o que está:
- **Implementado** (ativo na baseline atual),
- **Parcialmente implementado** (usável com limitações explícitas),
- **Em consolidação** (estabilização/endurecimento de capacidades já existentes),
- **Futuro** (direção planejada, sem compromisso de data de entrega).

## 1) Implementado

- Fluxo científico com inferência assistiva, fila de revisão e ciclo de validação humana.
- Superfícies operacionais de saúde de integrações (painel + APIs admin).
- Endpoints de paridade mobile e baseline de suporte a campo online/offline.
- Integrações do domínio ambiental (MapBiomas/contexto climático) e fluxos associados de monitoramento.
- Estrutura canônica bilíngue de documentação (`docs/en` + `docs/pt-BR`).

## 2) Parcialmente implementado

- Recursos avançados de identificação (cadeias multi-fonte/fallback) com dependência de provedor/configuração.
- Suporte mobile de pacotes offline seletivos e auto-detecção avançada com restrições operacionais.
- Algumas sondas de integração com profundidade de verificação limitada por contrato/provedor atual.
- Famílias de endpoint legadas/coexistentes ainda em harmonização.

## 3) Em consolidação (foco de curto prazo)

- Melhorar qualidade de observabilidade (diagnóstico de incidentes, tendências de latência/falha e playbooks operacionais).
- Fortalecer métricas de governança de revisão (interpretação de concordância/divergência e sinais de suporte ao revisor).
- Expandir cobertura de regressão em fronteiras sensíveis (permissões, integrações, edge cases do ciclo científico).
- Prosseguir limpeza de documentação canônica, reduzindo sobreposição legada.

## 4) Direção futura

- Analíticas de qualidade mais fortes para resultados de validação científica (além de contadores básicos de dashboard).
- Ferramental melhor para operação em triagem de incidentes cross-domain (identificação, enriquecimento, clima/ambiental).
- Modularização progressiva de domínios para reduzir concentração no app `mapping`.
- Refinamento adicional da UX mobile para fluxos de campo em cenários de conectividade restrita.

## 5) Expectativa de entrega

- Itens em “Implementado” compõem a baseline.
- Itens “Parcialmente implementado” devem ser tratados como disponíveis com limites operacionais.
- Itens “Em consolidação” são prioridade ativa e podem entrar de forma incremental.
- Itens de “Futuro” são direcionais e podem mudar conforme prioridades científicas/operacionais.
