# Evolução técnica do app mobile com compatibilidade total ao web

## 1) Diagnóstico da arquitetura atual

Principais incompatibilidades identificadas entre mobile e web:

1. **Contrato de API inconsistente**
   - Endpoint mobile apontava para `cadastrar_ponto_api/` (não encontrado nas URLs atuais).
   - `offlineService` usava `api.get()`/`api.post()` sem existir cliente HTTP real.
   - Formatos de `localizacao` divergentes (`[lng,lat]` no app vs GeoJSON em parte da API).

2. **Offline incompleto e não resiliente**
   - Cache anterior era apenas em memória (`offlineStorage` perdia dados ao fechar o app).
   - Não havia fila persistente com deduplicação, tentativas e log operacional.

3. **Navegação com rotas quebradas**
   - Home chamava `Alertas`/`Profile`, mas stack expunha outras rotas.

4. **Módulos estratégicos ausentes**
   - Base local de espécies foco sem estrutura uniforme para filtro e prioridade.
   - Sem trilha de inferência IA auditável para revisão humana.
   - Sem modelo modular de ingestão de missões/lotes de drone.

## 2) Estratégia segura de implementação (sem quebrar o existente)

1. Criar **camada base de integração** (HTTP + storage + sync) sem remover telas atuais.
2. Padronizar payloads mobile para o **contrato web existente**.
3. Introduzir recursos avançados como **módulos desacoplados** (IA, espécies foco, drone).
4. Manter comportamento antigo compatível, mas com fallback offline persistente.

## 3) Implementação entregue nesta etapa

### 3.1 Camada de dados e API
- `mobile/src/config/api.js`
  - centraliza URL base e endpoints reais do backend atual.
  - corrige rota de cadastro para `/api/pontos/`.
- `mobile/src/services/httpClient.js`
  - cliente HTTP unificado com token opcional e `credentials: include`.

### 3.2 Offline real + sincronização
- `mobile/src/services/offlineStorage.js`
  - persistência com `AsyncStorage` para cache, fila, logs, histórico IA e missões.
  - normalização de coordenadas e deduplicação de fila por chave idempotente.
- `mobile/src/services/offlineService.js`
  - cadastro online/offline com fallback automático.
  - sincronização resiliente com retry e logs.
  - sincronização incremental de referência via `/api/offline-sync/`.

### 3.3 Fluxo de campo e UX operacional
- `mobile/src/screens/CadastroPontoScreen.js`
  - registro funciona online/offline, com enfileiramento local.
  - botão de sugestão por IA offline para pré-preenchimento.
- `mobile/src/screens/MapScreen.js`
  - busca via camada offline e suporta localizacao array/GeoJSON.
- `mobile/src/screens/HomeScreen.js`
  - indicador claro de estado online/offline e pendências.
- `mobile/App.js`
  - sincronização automática ativa e rotas alinhadas com as telas.

### 3.4 Espécies foco + IA + drone (base estrutural)
- `mobile/src/services/speciesFocusService.js`
  - base local de espécies foco com campos exigidos e filtros.
- `mobile/src/services/aiAssistService.js`
  - inferência offline auditável (versão de modelo, confiança, coordenada, imagem, revisão humana).
- `mobile/src/services/droneMissionService.js`
  - modelo inicial para missão e lote de captura georreferenciada.

## 4) Ordem recomendada para continuidade

1. Validar autenticação mobile com backend (token/sessão) e fixar contrato único.
2. Conectar tela de gestão de espécies foco ao `speciesFocusService`.
3. Integrar revisão humana de inferências IA no fluxo científico (`/api/cientifico/*`).
4. Criar tela de missões/lotes de drone usando `droneMissionService`.
5. Adicionar testes automatizados de sync/offline (unit + integração).

## 5) Cuidados para não quebrar o web

- Não alterar modelos centrais no backend sem migração versionada.
- Não mudar nomes de campos canônicos (`nome_popular`, `nome_cientifico`, `status_validacao`, `localizacao`).
- Evitar duplicar regra de validação que já existe no backend; no app usar pré-validação leve.
- Manter rastreabilidade de IA sempre com revisão humana pendente por padrão.

## 6) Testes funcionais recomendados

### Testes online
- Login e carregamento do mapa (`/api/pontos/`).
- Cadastro de ponto com geolocalização e imagem.
- Sincronização de referências (`/api/offline-sync/`).

### Testes offline
- Criar 3 cadastros em modo avião.
- Fechar e reabrir app (dados pendentes devem persistir).
- Voltar conexão e validar esvaziamento da fila.
- Conferir logs de sync e ausência de duplicidade.

### Testes de IA assistida
- Gerar sugestão com base local carregada.
- Verificar gravação em histórico com `model_version`, confiança e status revisão.

### Testes de preparação drone
- Registrar missão + lote com imagens/pontos.
- Validar persistência local e estado pendente.

## 7) Nova funcionalidade: base offline direcionada de espécies + detecção automática

### Componentes adicionados/ajustados
- `mobile/src/services/speciesFocusService.js`
  - busca espécies disponíveis nas integrações existentes (`/api/plantas-offline/disponiveis/`)
  - salva seleção manual de espécies
  - estima pacote offline
  - gera base offline local com metadados, versão e hash de integridade
- `mobile/src/services/autoDetectionService.js`
  - usa base offline + IA heurística local para detecção assistida/automática
  - aplica cooldown anti-duplicidade
  - captura geolocalização
  - cria registro automático em fluxo offline/online com status pendente de revisão
  - marca ponto automaticamente no cache do mapa
- `mobile/src/services/offlineStorage.js`
  - novos blocos para metadados da base (`SPECIES_BASE_META`) e histórico de detecções
- `mobile/src/screens/PlantasOfflineScreen.js`
  - passa a exibir status da base offline direcionada e gera base após download selecionado
- `mobile/src/screens/IdentificarPlantaScreen.js`
  - novo fluxo de detecção automática offline com criação de registro rastreável

### Garantias de compatibilidade
- Não valida automaticamente o registro como científico definitivo
- Mantém registro como pendente/revisável
- Reaproveita endpoint e estrutura já existentes para pontos/sync
- Mantém sincronização posterior via fila offline
