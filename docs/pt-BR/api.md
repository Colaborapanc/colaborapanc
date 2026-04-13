# API

## Escopo

Este guia canônico de API descreve a superfície HTTP ativa do ColaboraPANC para backend, frontend web, app mobile, integrações e fluxos operacionais/admin.

**Fonte de verdade de roteamento:** `mapping/urls.py` (carregado por `config/urls.py`).

## 1) URL base, composição e convenções

- URL base local: `http://localhost:8000`
- Composição de rotas:
  - `config/urls.py` inclui `mapping.urls` na raiz.
  - Rotas de API e web coexistem na mesma árvore.
- Rotas web de conta (django-allauth): `/accounts/*`
- Healthcheck da plataforma: `GET /healthz/`

### Modelo de autenticação

- Login por token/sessão: `POST /api/token/login/`
- Criação de conta: `POST /api/register/`
- Maioria dos recursos exige `IsAuthenticated`.
- Rotas de revisão científica exigem perfil revisor/admin.
- Alguns endpoints operacionais exigem staff/superuser.

### Tags de maturidade usadas abaixo

- **Estável**: rota central com caminho de código ativo e contrato consolidado.
- **Legado compatível**: mantida por compatibilidade com superfícies mais novas coexistentes.
- **Operacional/Admin**: uso de administração, observabilidade e suporte.
- **Em evolução**: domínio ativo com contrato ainda amadurecendo.

## 2) Grupos de endpoints por domínio funcional

## 2.1 Domínio de identidade e conta

| Endpoint | Método | Auth | Finalidade | Entrada principal | Retorno esperado | Maturidade |
|---|---|---|---|---|---|---|
| `/api/token/login/` | POST | AllowAny | Login por token + sessão | `username` ou `email`, `password` | `token`, `user_id`, `username` | Estável |
| `/api/register/` | POST | AllowAny | Criar conta e token | `nome`, `email`, `password` | `token`, `user_id`, `username` | Estável |
| `/api/user/profile/` | GET | Autenticado | Resumo do perfil do usuário atual | – | perfil + estatísticas | Estável |
| `/api/user/change-password/` | POST | Autenticado | Alterar senha e rotacionar token | `senha_atual`, `nova_senha` | detalhe de sucesso + novo token | Estável |
| `/accounts/*` | GET/POST | Sessão/Web | Gestão de conta via allauth | formulários allauth | fluxo HTML/conta | Estável |

## 2.2 Domínio de pontos, contribuição e dados centrais

### Endpoints de recurso

| Endpoint | Método(s) | Auth | Finalidade | Principais params/body | Retorno esperado | Maturidade |
|---|---|---|---|---|---|---|
| `/api/pontos/` | GET, POST | Misto (create normalmente autenticado) | Listar/criar pontos georreferenciados | `nome_popular`, `localizacao`, campos científicos/alimentares opcionais | `PontoPANC` serializado | Estável |
| `/api/pontos/<id>/` | GET, PUT, PATCH, DELETE | Sensível a auth | Consultar/atualizar/remover ponto | payload do ponto | ponto serializado / status | Estável |
| `/api/pontos/<id>/enriquecimento/` | POST | Autenticado | Disparar enriquecimento de um ponto | contexto opcional | payload de enriquecimento | Estável |
| `/api/pontos/<id>/revalidar/` | POST | Autenticado | Disparar revalidação de um ponto | – | payload de revalidação | Estável |
| `/api/pontos/revalidar-lote/` | POST | Autenticado/uso admin | Revalidação em lote | `ids` (opcional), `limite` | resumo/resultados em lote | Operacional/Admin-like |
| `/api/compartilhamentos/` | GET, POST, ... | Auth | Recurso de compartilhamento | campos do modelo | payload de recurso DRF | Estável |

### Busca/utilidades de apoio

| Endpoint | Método | Auth | Finalidade | Principais params | Retorno esperado | Maturidade |
|---|---|---|---|---|---|---|
| `/api/busca-avancada/` | GET | AllowAny | Busca filtrada de pontos | filtros de nome/local/status/bbox | lista filtrada de pontos | Estável |
| `/api/plantas/` | GET | AllowAny | Listagem de plantas referenciais | `nome`, `bioma`, `origem` | lista de plantas | Estável |
| `/api/autocomplete-nome/` | GET | AllowAny | Sugestões de nome popular | `term` (+ modo detalhado opcional) | lista de sugestões | Legado compatível + Estável |
| `/api/nome-cientifico/` | GET | AllowAny | Resolver nome científico | `nome_popular` | payload de resolução | Legado compatível + Estável |
| `/api/geocode/` | POST | AllowAny | Utilitário de geocodificação reversa | payload de localização | resultado de geocode | Legado compatível |

## 2.3 Domínio de revisão e validação científica (`/api/cientifico/*`)

| Endpoint | Método | Auth | Finalidade | Principais params/body | Retorno esperado | Maturidade |
|---|---|---|---|---|---|---|
| `/api/cientifico/pontos/<ponto_id>/inferencia/` | POST | Autenticado | Executar inferência IA sobre imagem de ponto | header opcional `X-PLANTID-KEY` | payload do registro `PredicaoIA` | Estável |
| `/api/cientifico/revisao/fila/` | GET | Revisor/Admin | Listar fila de revisão | `confianca`, `status_fluxo`, `dias` | pontos filtrados em estados de revisão | Estável |
| `/api/cientifico/revisao/pontos/<ponto_id>/` | GET | Revisor/Admin | Detalhe de revisão de um ponto | `ponto_id` | ponto + última predição + última validação + histórico | Estável |
| `/api/cientifico/pontos/<ponto_id>/validacao/` | POST | Revisor/Admin | Decisão humana de validação | `decisao_final`, comentários/espécie opcionais | payload `ValidacaoEspecialista` | Estável |
| `/api/cientifico/pontos/<ponto_id>/historico/` | GET | Revisor/Admin | Histórico de decisões/eventos científicos | `ponto_id` | lista de histórico | Estável |
| `/api/cientifico/dashboard/` | GET | Autenticado | Resumo analítico científico | – | métricas/distribuições/amostra de priorização | Estável |

## 2.4 Domínio de comunicação, preferências e rotas

### Recursos DRF por router (primários)

| Endpoint | Método(s) | Auth | Finalidade | Entrada principal | Retorno esperado | Maturidade |
|---|---|---|---|---|---|---|
| `/api/notificacoes/` | GET, POST, PATCH... + actions | Autenticado | Ciclo de notificações do usuário | payload de notificação/ação | notificações e resultados de ação | Estável |
| `/api/dispositivos-push/` | GET, POST, PATCH... | Autenticado | Ciclo de token de dispositivo push | `token`, `plataforma` | payload de registro de dispositivo | Estável |
| `/api/conversas/` | GET, POST, ... | Autenticado | Ciclo de conversas | identificadores de participante | payload de conversa | Estável |
| `/api/mensagens/` | GET, POST, ... | Autenticado | Ciclo de mensagens | `conversa_id`, `conteudo` | payload de mensagem | Estável |
| `/api/preferencias/` | GET, POST, PATCH | Autenticado | Preferências de usuário | campos de preferência | payload de preferência | Estável |
| `/api/recomendacoes/` | GET (+ action) | Autenticado | Recomendações personalizadas | payload de ação em recomendação | lista/payload de recomendações | Estável |
| `/api/rotas/` | GET, POST, PATCH... | Autenticado | Registros de rotas | campos de rota | payload de rota | Estável |

### Endpoints de compatibilidade (`views.py`)

| Endpoint | Método | Auth | Finalidade | Maturidade |
|---|---|---|---|---|
| `/api/push-token/` | POST | Misto | Fluxo legado de push | Legado compatível |
| `/api/notificacoes/` | GET | Misto | Listagem legada de notificações | Legado compatível |
| `/api/conversas/` | GET | Misto | Listagem legada de conversas | Legado compatível |
| `/api/mensagens/` | GET | Misto | Listagem legada de mensagens | Legado compatível |
| `/api/compartilhamentos/` | POST | Misto | Fluxo legado de compartilhamento | Legado compatível |

## 2.5 Domínio de AR e identificação avançada

| Endpoint | Método(s) | Auth | Finalidade | Entrada principal | Retorno esperado | Maturidade |
|---|---|---|---|---|---|---|
| `/api/identificar-planta/` | POST | AllowAny/Auth (dependendo do contexto) | Identificação avançada por imagem | imagem + opções | payload de identificação | Em evolução |
| `/api/buscar-plantas/` | GET | AllowAny | Busca de plantas no fluxo avançado | termos de consulta | resultados de busca | Em evolução |
| `/api/modelos-ar-disponiveis/` | GET | AllowAny | Catálogo público de modelos AR | filtros opcionais | lista de modelos AR | Em evolução |
| `/api/plantas-customizadas/` | CRUD | Auth | Recurso de plantas customizadas | campos do modelo | payload de recurso DRF | Em evolução |
| `/api/modelos-ar/` | CRUD | Auth | Recurso de modelos AR | campos do modelo | payload de recurso DRF | Em evolução |
| `/api/historico-identificacao/` | GET | Auth | Histórico de identificação | filtros opcionais | registros históricos | Em evolução |
| `/api/referencias-ar/` | CRUD | Auth | Recurso de referências AR | campos do modelo | payload de recurso DRF | Legado compatível/Em evolução |

## 2.6 Domínio de espécies offline e paridade mobile

### APIs de inventário/download offline de espécies

| Endpoint | Método(s) | Auth | Finalidade | Principais params/body | Retorno esperado | Maturidade |
|---|---|---|---|---|---|---|
| `/api/especies-referenciais/busca/` | GET | AllowAny/Auth | Busca canônica de espécies referenciais | termos de consulta | lista normalizada de espécies | Estável |
| `/api/especies-referenciais/busca-recursiva/` | GET | AllowAny/Auth | Busca recursiva expandida de espécies | termos de consulta | conjunto expandido de resultados | Em evolução |
| `/api/plantas-offline/disponiveis/` | GET | Auth | Listar espécies disponíveis para download | filtros | lista de disponibilidade | Estável |
| `/api/plantas-offline/pacotes/` | GET | Auth | Listar pacotes offline predefinidos | – | lista de pacotes | Estável |
| `/api/plantas-offline/pacotes/<pacote_id>/baixar/` | POST | Auth | Baixar pacote predefinido | `pacote_id` | payload do pacote | Estável |
| `/api/plantas-offline/baixar/` | POST | Auth | Baixar seleção de espécies | payload de seleção | payload de espécies selecionadas | Estável |
| `/api/plantas-offline/<planta_id>/dados/` | GET | Auth | Obter payload offline de uma espécie | `planta_id` | payload da espécie | Estável |
| `/api/plantas-offline/minhas/` | GET | Auth | Listar baixadas do usuário | – | lista do usuário | Estável |
| `/api/plantas-offline/<planta_id>/remover/` | POST | Auth | Remover espécie baixada | `planta_id` | payload de status | Estável |
| `/api/plantas-offline/configuracoes/` | GET, POST | Auth | Ler/atualizar configuração offline | payload de configuração | payload de configuração | Estável |
| `/api/plantas-offline/sincronizar/` | POST | Auth | Sincronizar estado offline | payload de sync | resumo de sincronização | Estável |

### APIs de paridade mobile (`/api/mobile/*`)

| Endpoint | Método | Auth | Finalidade | Principais params/body | Retorno esperado | Maturidade |
|---|---|---|---|---|---|---|
| `/api/mobile/identificacao/imagem/` | POST | Autenticado | Contrato canônico mobile de identificação por imagem | imagem multipart (`imagem`/`foto`), toggles opcionais | payload normalizado de identificação | Estável |
| `/api/mobile/mapa/previews/` | GET | Autenticado | Payload canônico de preview de mapa para mobile | `q`, `limite` | `{total, resultados[]}` | Estável |
| `/api/mobile/offline/base/metadata/` | GET | Autenticado | Metadados/versionamento da base offline | – | metadados de versão/contagem | Estável |
| `/api/mobile/offline/base/` | GET | Autenticado | Exportar payload da base offline | `limite`, `busca` | metadata + payload de espécies | Estável |

## 2.7 Domínio ambiental e territorial

### Endpoints MapBiomas

| Endpoint | Método | Auth | Finalidade | Retorno esperado | Maturidade |
|---|---|---|---|---|---|
| `/api/mapbiomas/alertas/` | GET | AllowAny/Auth | consultar alertas de desmatamento | payload de alertas | Estável/Em evolução |
| `/api/mapbiomas/alertas/<alert_code>/` | GET | AllowAny/Auth | detalhar alerta por código | payload detalhado do alerta | Estável/Em evolução |
| `/api/mapbiomas/territorios/` | GET | AllowAny/Auth | consultar territórios | payload de territórios | Estável/Em evolução |
| `/api/mapbiomas/propriedade/` | GET | AllowAny/Auth | consulta por propriedade/CAR | payload de alertas por propriedade | Estável/Em evolução |
| `/api/mapbiomas/ponto/` | GET | AllowAny/Auth | consulta contextual por ponto | payload contextual | Estável/Em evolução |
| `/api/mapbiomas/pontos-panc/<ponto_id>/` | GET | AllowAny/Auth | alertas próximos para ponto | payload ponto-alerta | Estável/Em evolução |
| `/api/mapbiomas/testar/` | GET | AllowAny/Auth | teste de conectividade | payload de status de teste | Operacional/Admin-like |

### Endpoints de clima

| Endpoint | Método | Auth | Finalidade | Principais params/body | Retorno esperado | Maturidade |
|---|---|---|---|---|---|---|
| `/api/alertas-ativos/` | GET | AllowAny | listar alertas climáticos ativos | `ponto_id`, `limit` | `{count, results[]}` | Estável |
| `/api/historico_alertas_api/` | GET | AllowAny | listar histórico de alertas climáticos | `ponto_id`/`ponto`, `limit` | `{count, results[]}` | Estável |
| `/api/clima/sincronizar/` | POST | Staff/Superuser | disparar sincronização climática | opcionais `ponto_id`, `only_active` | resumo created/updated/skipped/errors | Operacional/Admin |
| `/api/clima/status/` | GET | Staff/Superuser | status operacional clima/ambiental | – | integrações + métricas de alerta | Operacional/Admin |

## 2.8 Domínio de enriquecimento taxonômico (`/api/enriquecimento/*`)

| Endpoint | Método | Auth | Finalidade | Principais params/body | Retorno esperado | Maturidade |
|---|---|---|---|---|---|---|
| `/api/enriquecimento/` | POST | AllowAny | enriquecer nome científico e opcionalmente vincular planta | `nome_cientifico`, opcional `planta_id` | payload de resultado de enriquecimento | Estável |
| `/api/enriquecimento/revalidar/` | POST | Autenticado | reexecutar enriquecimento para planta existente | `planta_id` | payload de revalidação | Estável |
| `/api/enriquecimento/<planta_id>/` | GET | AllowAny | consultar payload enriquecido de uma planta | `planta_id` | payload de planta enriquecida | Estável |
| `/api/enriquecimento/<planta_id>/historico/` | GET | AllowAny | consultar histórico de enriquecimentos | `planta_id` | lista histórica | Estável |

## 2.9 Domínio de administração de integrações e operações

| Endpoint | Método | Auth | Finalidade | Principais params/body | Retorno esperado | Maturidade |
|---|---|---|---|---|---|---|
| `/api/admin/integracoes/health/` | GET | Auth + validação admin | status consolidado das integrações | – | lista/status de integrações | Operacional/Admin |
| `/api/admin/integracoes/testar/` | POST | Auth + validação admin | executar sonda(s) de integração | opcional `integration_name` | resumo de execução + `resultados[]` | Operacional/Admin |
| `/painel-admin/integracoes/` | GET/POST | acesso web admin | painel operacional de integrações | seletor opcional de integração | dashboard HTML | Operacional/Admin |

## 3) Watchlist de legados/experimentais

Trate os itens abaixo como superfícies de compatibilidade ou maturidade parcial:

- coexistência de recursos router com endpoints de compatibilidade baseados em função no namespace de comunicação,
- fluxo híbrido legado `/api/identificar/` coexistindo com contratos científicos e avançados,
- fluxos de AR/customização e busca recursiva de espécies marcados como em evolução,
- árvore de rotas mista web/API contendo páginas operacionais admin.

## 4) Expectativas padrão de resposta e erro

- `200/201`: operação concluída com sucesso.
- `400`: falha de validação/regra de negócio.
- `401/403`: falha de autenticação/autorização.
- `404`: recurso não encontrado.
- `503`: integração upstream indisponível (notável em provedores de inferência).

## 5) Anexo técnico sugerido (recomendado)

Para evitar poluir este guia canônico e ainda manter inventário completo, recomenda-se anexos dedicados de inventário, por exemplo:

- `docs/en/api-endpoint-inventory.md`
- `docs/pt-BR/api-inventario-endpoints.md`

Estrutura recomendada do anexo:
- lista exaustiva de endpoints,
- schemas de request/response por rota,
- mapa de serializers/services,
- tags de maturidade e compatibilidade,
- notas de depreciação e trilha de migração.
