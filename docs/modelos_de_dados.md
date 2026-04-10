# Modelos de dados

## Núcleo de domínio

### `PontoPANC`
- Finalidade: registro georreferenciado de observação de PANC.
- Campos-chave: `planta`, `criado_por`, `localizacao`, `foto`, `status_identificacao`, `status_validacao`, `status_fluxo`.
- Regras: validação geográfica para coordenadas aproximadas do Brasil no `clean()`.

### `PlantaReferencial`
- Finalidade: catálogo botânico base.
- Campos: nome popular/científico, parte comestível, bioma, origem, fonte.

### `HistoricoIdentificacao`
- Finalidade: rastrear tentativas de identificação (método, score, sucesso, erro, tempo).

### `PredicaoIA`
- Finalidade: persistir predição estruturada (top-k e confiança) vinculada ao ponto.

### `ValidacaoEspecialista`
- Finalidade: decisão humana final por revisor.
- Campos: `decisao_final`, `especie_final`, `motivo_divergencia`, `observacao`.

### `HistoricoValidacao`
- Finalidade: trilha de auditoria de eventos do fluxo científico.

## Outros domínios relevantes
- **Gamificação**: `Badge`, `Missao`, `MissaoUsuario`, `PontuacaoUsuario`, `HistoricoGamificacao`, `RankingRevisor`.
- **Comunicação**: `Notificacao`, `DispositivoPush`, `Conversa`, `Mensagem`.
- **Território e risco**: `AlertaClimatico`.
- **Rotas e visitas**: `Rota`, `RotaPonto`, `RoteiroPANC`, `RoteiroPANCItem`.
- **Offline**: `PacotePlantasOffline`, `PlantaOfflineUsuario`, `ConfiguracaoOffline`, `CacheOffline`.
- **AR e customização**: `PlantaCustomizada`, `ModeloAR`, `ReferenciaAR`.

## Status e rastreabilidade
- `status_fluxo` do ponto controla ciclo científico (`rascunho`, `submetido`, `em_revisao`, `validado`, `rejeitado`, `necessita_revisao`).
- `status_validacao` mantém camada operacional (`pendente`, `aprovado`, `reprovado`, `pendencia`).
