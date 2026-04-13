# Data models

## Domain Core

### `PontoPANC`
- Purpose: georeferenced record of PANC observation.
- Key fields: `planta`, `criado_por`, `localizacao`, `foto`, `status_identificacao`, `status_validacao`, `status_fluxo`.
- Rules: geographic validation for approximate coordinates of Brazil in `clean()`.

### `PlantaReferencial`
- Purpose: basic botanical catalogue.
- Fields: popular/scientific name, edible part, biome, origin, source.

### `HistoricoIdentificacao`
- Purpose: to track identification attempts (method, score, success, error, time).

### `PredicaoIA`
- Purpose: persist structured prediction (top-k and confidence) linked to the point.

### `ValidacaoEspecialista`
- Purpose: final human decision by reviewer.
- Fields: `decisao_final`, `especie_final`, `motivo_divergencia`, `observacao`.

### `HistoricoValidacao`
- Purpose: audit trail of scientific flow events.

## Other relevant domains
- **Gamification**: `Badge`, `Missao`, `MissaoUsuario`, `PontuacaoUsuario`, `HistoricoGamificacao`, `RankingRevisor`.
- **Communication**: `Notificacao`, `DispositivoPush`, `Conversa`, `Mensagem`.
- **Territory and risk**: `AlertaClimatico`.
- **Routes and visits**: `Rota`, `RotaPonto`, `RoteiroPANC`, `RoteiroPANCItem`.
- **Offline**: `PacotePlantasOffline`, `PlantaOfflineUsuario`, `ConfiguracaoOffline`, `CacheOffline`.
- **AR and customization**: `PlantaCustomizada`, `ModeloAR`, `ReferenciaAR`.

## Status and traceability
- `status_fluxo` of the point controls scientific cycle (`rascunho`, `submetido`, `em_revisao`, `validado`, `rejeitado`, `necessita_revisao`).
- `status_validacao` maintains operational layer (`pendente`, `aprovado`, `reprovado`, `pendencia`).
