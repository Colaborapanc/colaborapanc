# Guia de Administração

## Escopo e separação de responsabilidades

Este guia canônico cobre o **uso administrativo e operacional** do ColaboraPANC.

Para manter governança clara e auditável, a documentação é separada em 3 camadas:

1. **Operação administrativa (este arquivo):** papéis, permissões, curadoria/revisão, operação de integrações, observabilidade e supervisão do fluxo científico.
2. **Governança algorítmica:** princípios, controles, riscos e mitigação para IA assistiva.
3. **Política de dados/privacidade:** classes de dados, minimização, retenção, controle de acesso e salvaguardas de privacidade.

### Anexos canônicos complementares
- Anexo de governança algorítmica: [`governanca-algoritmica-admin.md`](./governanca-algoritmica-admin.md)
- Anexo de política de dados/privacidade: [`politica-dados-privacidade-admin.md`](./politica-dados-privacidade-admin.md)

## 1) Superfícies administrativas

- Admin Django: `/admin/`
- Painel de integrações: `/painel-admin/integracoes/`
- Painel de validação: `/painel-validacao/`
- Admin de gamificação: `/gamificacao/admin/`
- APIs administrativas de integrações:
  - `GET /api/admin/integracoes/health/`
  - `POST /api/admin/integracoes/testar/`

## 2) Papéis e permissões

## 2.1 Perfis administrativos
- **`is_staff` / `is_superuser`:** acesso a painéis administrativos e APIs de operação de integrações.
- **Permissões de revisor/admin:** ações de revisão científica são protegidas por controles de papel (ex.: checagens de revisor e `IsReviewerOrAdmin` nos endpoints científicos).

## 2.2 Fronteiras operacionais de permissão
- Operação de integrações (health/teste) é restrita a perfis administrativos.
- Ações de validação científica são restritas a papéis autorizados de revisor/admin.
- Exportações sensíveis e comandos operacionais devem ser executados apenas por operadores confiáveis.

## 3) Operação de curadoria e revisão humana

## 3.1 Ciclo de curadoria científica (visão admin)
1. Inspecionar pontos pendentes e estado da fila.
2. Revisar evidências de imagem/inferência.
3. Aprovar/rejeitar/solicitar nova revisão.
4. Registrar justificativa de divergência quando IA e decisão humana diferirem.
5. Confirmar persistência de artefatos de rastreabilidade.

## 3.2 Regra de governança
- Saídas de IA são **assistivas**.
- Decisão científica final é **humana** e deve permanecer auditável.

## 4) Operação de integrações

## 4.1 Responsabilidades no painel de integrações
- Monitorar saúde (`online`, `degradada/parcial`, `offline`, `nao_configurada`).
- Acionar teste completo ou por integração.
- Inspecionar diagnósticos amigáveis (`mensagem_amigavel`, `error_type`), último sucesso/falha e nível de latência.

## 4.2 Triagem operacional típica
1. Verificar status e variáveis de ambiente ausentes.
2. Separar falha de credencial/configuração de indisponibilidade de rede/provedor.
3. Reexecutar teste da integração afetada.
4. Aplicar tratamento de incidente com fallback por domínio (identificação, enriquecimento, clima/ambiental).
5. Registrar contexto do incidente e ação de correção.

## 5) Supervisão de fluxos científicos

## 5.1 Pontos de controle
- Estado de geração de inferência.
- Vazão da fila e volume pendente.
- Resultado de validações (`validado`, `rejeitado`, `necessita_revisao`).
- Sinais de divergência humano/IA.
- Status de enriquecimento e comportamento em falha parcial.

## 5.2 Métricas de supervisão (operacionais)
- Taxa de validação/rejeição.
- Tendência de concordância/divergência.
- Tempo médio até validação.
- Distribuição por faixa de confiança.

## 6) Observabilidade e rastreabilidade

## 6.1 Observabilidade operacional
- Usar painel e endpoints administrativos como primeiro sinal operacional.
- Acompanhar latência e transições de status ao longo do tempo.
- Conduzir troubleshooting orientado por impacto de domínio.

## 6.2 Requisitos de rastreabilidade
- Preservar eventos de histórico científico e registros de validação.
- Preservar resultados de testes de integração e metadados de última falha.
- Manter auditável a decisão do revisor, justificativas de divergência e cronologia de decisão.

## 7) Comandos operacionais de base (exemplos)

- `python manage.py auditar_integracoes_funcionais`
- `python manage.py sincronizar_alertas_climaticos`
- `python manage.py sincronizar_alertas_ambientais`
- `python manage.py processar_plantas`

Comandos de gestão devem ser tratados como procedimento operacional controlado, com execução restrita por papel e registro de auditoria.

## 8) O que fica fora deste arquivo

Para não misturar responsabilidades:
- Governança de IA (princípios/riscos/mitigações) fica em [`governanca-algoritmica-admin.md`](./governanca-algoritmica-admin.md).
- Política de dados e privacidade (base técnica alinhada à LGPD) fica em [`politica-dados-privacidade-admin.md`](./politica-dados-privacidade-admin.md).
