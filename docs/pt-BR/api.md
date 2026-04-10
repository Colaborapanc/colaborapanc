# API

## Escopo

Este guia canônico de API documenta a superfície HTTP ativa do ColaboraPANC para:

- backend/web clients,
- frontend web,
- app mobile,
- ferramentas de integração e operação.

Registro autoritativo de rotas: `mapping/urls.py` (incluído por `config/urls.py`).

## 1) URL base e modelo de roteamento

- URL base local: `http://localhost:8000`
- Composição raiz de URLs:
  - `config/urls.py` inclui `mapping.urls` na raiz.
  - `mapping/urls.py` mistura rotas web e rotas de API.
- Fluxo de conta/autenticação web (allauth): `/accounts/*`
- Endpoint de health: `GET /healthz/`

## 2) Modelo de autenticação e autorização

### 2.1 Fluxos principais de auth
- `POST /api/token/login/`
  - Finalidade: obter token DRF e sessão.
  - Body: `username|email`, `password`.
  - Retorno: `token`, `user_id`, `username`.
- `POST /api/register/`
  - Finalidade: criar conta + emitir token.
  - Body: `nome`, `email`, `password`.
  - Retorno: `token`, `user_id`, `username`.

### 2.2 Perfil/conta autenticada
- `GET /api/user/profile/`
- `POST /api/user/change-password/`

### 2.3 Níveis de permissão usados na API
- **Público (`AllowAny`)**: entradas selecionadas de busca/leitura e enriquecimento.
- **Autenticado (`IsAuthenticated`)**: maioria dos endpoints operacionais.
- **Revisor/Admin (`IsReviewerOrAdmin`)**: endpoints de revisão/validação científica.
- **Staff/Superuser**: endpoints administrativos de sync/status climático e testes de integração.

## 3) Legenda de maturidade de endpoint

- **Estável**: rota central com uso ativo e backing explícito de serviço/serializer.
- **Legado compatível**: rota mantida para compatibilidade enquanto contratos novos coexistem.
- **Operacional/Admin**: endpoints voltados a administração, observabilidade e suporte.
- **Em evolução**: família de rotas em evolução ativa (contrato ainda amadurecendo).

## 4) Grupos funcionais de endpoints

## 4.1 Domínio de pontos e contribuição

### Endpoints de recurso por router (`/api/` via DRF)
- `/api/pontos/` (**Estável**, create/update sensível a auth)
  - Finalidade: listar/criar/atualizar pontos PANC georreferenciados.
  - Principais campos no create:
    - nomenclatura: `nome_popular`, variações opcionais de nome científico,
    - geodado: `localizacao` (`[lng,lat]` ou objeto), opcional `latitude`/`longitude`,
    - campos manuais opcionais de comestibilidade/sazonalidade,
    - toggle `enriquecer_automaticamente`.
  - Retorno: serialização `PontoPANC` com campos de ciclo/enriquecimento.
- `/api/pontos/<id>/enriquecimento/` (**Estável**, action)
- `/api/pontos/<id>/revalidar/` (**Estável**, action)
- `/api/pontos/revalidar-lote/` (**Operacional/Admin-like**, action em lote)
- `/api/compartilhamentos/` (**Estável**, recurso de colaboração)

### Rotas auxiliares de busca/nome
- `GET /api/busca-avancada/` (**Estável**)
- `GET /api/plantas/` (**Estável**)
- `GET /api/autocomplete-nome/` (**Legado compatível + Estável**)
- `GET /api/nome-cientifico/` (**Legado compatível + Estável**)
- `POST /api/geocode/` (**Utilitário legado compatível**)

## 4.2 Domínio do fluxo científico (`/api/cientifico/*`)

- `POST /api/cientifico/pontos/<ponto_id>/inferencia/` (**Estável**, autenticado)
  - Finalidade: executar inferência IA sobre imagem de ponto existente.
  - Comportamento principal:
    - valida ponto/imagem,
    - chama serviço IA multi-provedor,
    - persiste `PredicaoIA`, atualiza status/score do ponto,
    - registra evento no histórico de validação.
  - Header opcional: `X-PLANTID-KEY`.
  - Retorno: payload `PredicaoIA`.
- `GET /api/cientifico/revisao/fila/` (**Estável**, revisor/admin)
  - Filtros de query: `confianca`, `status_fluxo`, `dias`.
- `GET /api/cientifico/revisao/pontos/<ponto_id>/` (**Estável**, revisor/admin)
  - Retorno: ponto, predição mais recente, última validação, histórico.
- `POST /api/cientifico/pontos/<ponto_id>/validacao/` (**Estável**, revisor/admin)
  - Body: `decisao_final` (`validado|rejeitado|necessita_revisao`), opcionais `especie_final`, `motivo_divergencia`, `observacao`.
  - Retorno: registro `ValidacaoEspecialista`.
- `GET /api/cientifico/pontos/<ponto_id>/historico/` (**Estável**, revisor/admin)
- `GET /api/cientifico/dashboard/` (**Estável**, analytics autenticado)

## 4.3 Domínio de comunicação, preferências e social

### Recursos por router (`views_api.py`)
- `/api/notificacoes/` (**Estável**)
  - Inclui ações customizadas como não-lidas e marcação de leitura.
- `/api/dispositivos-push/` (**Estável**)
- `/api/conversas/` (**Estável**)
- `/api/mensagens/` (**Estável**)
- `/api/preferencias/` (**Estável**)
- `/api/recomendacoes/` (**Estável**, foco leitura)
- `/api/rotas/` (**Estável**)

### Endpoints companheiros legados (`views.py`)
- `POST /api/push-token/`
- `GET /api/notificacoes/`
- `GET /api/conversas/`
- `GET /api/mensagens/`
- `POST /api/compartilhamentos/`

> Observação: endpoints de router e legados coexistem neste domínio e devem ser tratados como superfície de compatibilidade.

## 4.4 Domínio de AR e identificação avançada

- `POST /api/identificar-planta/` (**Em evolução**)
- `GET /api/buscar-plantas/` (**Em evolução**)
- `GET /api/modelos-ar-disponiveis/` (**Em evolução**)
- `/api/plantas-customizadas/` (recurso DRF, **Em evolução**)
- `/api/modelos-ar/` (recurso DRF, **Em evolução**)
- `/api/historico-identificacao/` (recurso orientado a leitura, **Em evolução**)
- `/api/referencias-ar/` (recurso de router em `views.py`, **Legado compatível/Em evolução**)

## 4.5 Domínio de offline de espécies e paridade mobile

### APIs de espécies offline
- `GET /api/especies-referenciais/busca/` (**Estável**)
- `GET /api/especies-referenciais/busca-recursiva/` (**Em evolução**)
- `GET /api/plantas-offline/disponiveis/` (**Estável**)
- `GET /api/plantas-offline/pacotes/` (**Estável**)
- `POST /api/plantas-offline/pacotes/<pacote_id>/baixar/` (**Estável**)
- `POST /api/plantas-offline/baixar/` (**Estável**)
- `GET /api/plantas-offline/<planta_id>/dados/` (**Estável**)
- `GET /api/plantas-offline/minhas/` (**Estável**)
- `POST /api/plantas-offline/<planta_id>/remover/` (**Estável**)
- `GET|POST /api/plantas-offline/configuracoes/` (**Estável**)
- `POST /api/plantas-offline/sincronizar/` (**Estável**)

### APIs de paridade mobile (`/api/mobile/*`)
- `POST /api/mobile/identificacao/imagem/` (**Estável**, autenticado)
  - Entrada: imagem multipart (`imagem` ou `foto`), opcionais `usar_custom_db`, `usar_google`.
  - Retorno: payload normalizado de identificação (`sucesso`, nomes botânicos/populares, score, flag de revisão pendente, metadados de candidatos).
- `GET /api/mobile/mapa/previews/` (**Estável**, autenticado)
  - Query: `q`, `limite`.
  - Retorno: cards leves de mapa para renderização mobile.
- `GET /api/mobile/offline/base/metadata/` (**Estável**, autenticado)
- `GET /api/mobile/offline/base/` (**Estável**, autenticado)
  - Query: `limite`, `busca`.

## 4.6 Domínio ambiental e territorial

### APIs MapBiomas (`/api/mapbiomas/*`)
- `GET /api/mapbiomas/alertas/`
- `GET /api/mapbiomas/alertas/<alert_code>/`
- `GET /api/mapbiomas/territorios/`
- `GET /api/mapbiomas/propriedade/`
- `GET /api/mapbiomas/ponto/`
- `GET /api/mapbiomas/pontos-panc/<ponto_id>/`
- `GET /api/mapbiomas/testar/`

Status: **Estável/Em evolução** (respostas dependentes de integração externa).

### APIs de clima
- `GET /api/alertas-ativos/` (**Estável**, leitura pública)
  - Query: `ponto_id`, `limit`.
- `GET /api/historico_alertas_api/` (**Estável**, leitura pública)
  - Query: `ponto_id|ponto`, `limit`.
- `POST /api/clima/sincronizar/` (**Operacional/Admin**, staff/superuser)
  - Body: opcionais `ponto_id`, `only_active`.
- `GET /api/clima/status/` (**Operacional/Admin**, staff/superuser)

## 4.7 Domínio de enriquecimento taxonômico (`/api/enriquecimento/*`)

- `POST /api/enriquecimento/` (**Estável**, entrada pública)
  - Body: `nome_cientifico`, opcional `planta_id`.
- `POST /api/enriquecimento/revalidar/` (**Estável**, autenticado)
  - Body: `planta_id`.
- `GET /api/enriquecimento/<planta_id>/` (**Estável**)
- `GET /api/enriquecimento/<planta_id>/historico/` (**Estável**)

## 4.8 Endpoints administrativos de integração e operação

- `GET /api/admin/integracoes/health/` (**Operacional/Admin**)
- `POST /api/admin/integracoes/testar/` (**Operacional/Admin**)
  - Body: opcional `integration_name`.
  - `integration_name` inválido retorna `400` com `valid_options`.
- `GET /painel-admin/integracoes/` (**Painel web Operacional/Admin**)

## 5) Endpoints legados/compatíveis e superfície mista para atenção

As áreas abaixo coexistem intencionalmente com contratos mais novos e devem ser tratadas como camada de compatibilidade:

- coexistência de router e endpoints de função em namespaces próximos (`/api/notificacoes`, `/api/conversas`, `/api/mensagens`, `/api/compartilhamentos`),
- rota legada/híbrida de identificação web (`/api/identificar/`) coexistindo com APIs científica e avançada,
- rotas web-form/admin expostas na mesma árvore de URL do projeto.

## 6) Expectativas padrão de resposta/erro

Códigos comuns nas famílias de endpoint:
- `200/201`: sucesso.
- `400`: falha de validação/regra de negócio.
- `401/403`: sem autenticação/sem autorização.
- `404`: recurso não encontrado.
- `503`: indisponibilidade de integração externa (notável em fallback de inferência IA).

## 7) Anexo técnico sugerido (recomendado)

Para manter este documento canônico legível sem perder rastreabilidade de inventário completo, recomenda-se manter anexo dedicado de inventário de endpoints e contratos, por exemplo:

- `docs/en/api-endpoint-inventory.md`
- `docs/pt-BR/api-inventario-endpoints.md`

Conteúdo sugerido do anexo:
- lista exaustiva de endpoints,
- schemas de request/response por rota,
- referência de serializers,
- tags de maturidade por endpoint,
- notas de depreciação/compatibilidade.
