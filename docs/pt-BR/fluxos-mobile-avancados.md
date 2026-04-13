# Fluxos Mobile e Recursos Avançados de Identificação

## Escopo

Este anexo técnico canônico consolida detalhes de fluxos mobile antes dispersos em documentos legados (`docs/pt/*` e `docs/en/*`).

Foco:
- arquitetura mobile Expo/React Native,
- identificação por imagem,
- revisão humana de dados originados no mobile,
- fila offline e sincronização,
- pacotes offline seletivos,
- IA assistiva,
- AR e recursos avançados de identificação.

## 1) Arquitetura mobile (Expo/React Native)

### 1.1 Fronteira contratual
- Registro de endpoints mobile centralizado em `mobile/src/config/api.js`.
- Camada de serviços (`mobile/src/services/*`) é a fronteira de integração com APIs backend.
- Telas (`mobile/src/screens/*`) devem consumir serviços, sem URL hardcoded.

### 1.2 Grupos centrais de serviços mobile
- **Identificação e suporte científico:** `identificacaoService.js`, `aiAssistService.js`.
- **Offline e sync:** `offlineService.js`, `offlineStorage.js`, `plantasOfflineService.js`.
- **Módulos avançados de captura:** `autoDetectionService.js`, `droneMissionService.js`.
- **API/auth/comunicação geral:** `httpClient.js`, `apiClient.js`, `authService.js`, serviços de mensagens/notificações.

## 2) Fluxo de identificação por imagem

1. Usuário captura/seleciona imagem no app.
2. Mobile envia payload de identificação para endpoints compartilhados.
3. Backend persiste contexto de predição e artefatos de confiança.
4. Resultado é tratado como saída assistiva (não verdade científica final).
5. Ponto permanece revisável no fluxo científico.

### Famílias de endpoint relacionadas
- `POST /api/mobile/identificacao/imagem/`
- `POST /api/cientifico/pontos/<id>/inferencia/`
- `POST /api/identificar-planta/` (entrada avançada/legado compatível)

## 3) Revisão humana no ciclo originado pelo mobile

- Saída de IA é intencionalmente **assistiva**.
- Decisão científica final é **validação humana** via endpoints protegidos.
- Divergência IA vs especialista deve permanecer auditável em modelos de histórico.

Operacionalmente, registros criados/enriquecidos via mobile devem passar por:
- fila de revisão,
- endpoints de validação por revisor/admin,
- endpoints de histórico/auditoria.

## 4) Offline e sincronização

### 4.1 Modelo de fila offline
- Armazenamento offline persiste pendências, logs de sincronização e metadados locais.
- Fila deve operar com idempotência/deduplicação e sync resiliente a falhas.
- Fechar/reabrir app não pode perder pendências.

### 4.2 Comportamento de sync
- Cadastro suporta online-first com fallback offline.
- Ao reconectar, fila pendente é reprocessada e marcada como sincronizada.
- App deve expor estado de pendência/sync para transparência operacional.

## 5) Pacotes offline seletivos

### 5.1 Objetivo dos pacotes
Pacotes seletivos entregam base mínima viável de espécies para uso em campo com baixa conectividade.

### 5.2 Superfície típica de API
- lista de disponíveis,
- lista de pacotes,
- download de pacote/espécie,
- lista do que usuário baixou,
- configuração offline,
- endpoints de sincronização de status.

### 5.3 Expectativas de compatibilidade
- Uso de pacote offline deve preservar campos canônicos de espécie.
- Registros originados offline continuam revisáveis e não devem ser auto-promovidos para validação científica final.

## 6) IA assistiva e heurísticas locais

- IA local/mobile pode pré-preencher ou sugerir espécies candidatas.
- Contexto de confiança deve ser registrado quando tecnicamente disponível.
- IA assistiva não pode contornar governança de revisão humana.
- Automação de detecção (quando usada) deve aplicar salvaguardas anti-duplicidade e manter estado revisável.

## 7) AR e recursos avançados de identificação

### 7.1 Superfície de capacidade AR
- Recursos AR são complementares (educacionais/operacionais).
- Artefatos 3D (quando disponíveis) permanecem opcionais e não bloqueiam fluxo núcleo de identificação.

### 7.2 Orquestração avançada de identificação
- Identificação multi-fonte pode combinar base local/custom com provedores externos.
- Cadeias de fallback são permitidas, mantendo decisão final humana.
- Variabilidade de saúde/credencial de provedores externos deve aparecer na observabilidade de integrações.

## 8) Política canônica e migração

Este anexo substitui narrativa fragmentada de fluxos mobile avançados. Documentos legados ficam como trilha histórica; atualizações canônicas devem ocorrer aqui e em:
- `docs/pt-BR/modulos.md`
- `docs/pt-BR/arquitetura.md`
- `docs/pt-BR/guia-do-usuario.md`
