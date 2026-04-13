# System scientific flow

## Main flow
`cadastro -> imagem -> inferência -> revisão -> validação -> métricas -> priorização territorial`

## 1. Point registration
- Entity: `PontoPANC`.
- Main data: plan, geographic location, textual context and photo.
- Typical initial state: `status_fluxo='rascunho'` and `status_validacao='pendente'`.
- Food/seasonal fields exposed in registration and editing:
- `comestibilidade_status` (__CODE1__/__CODE2__/__CODE3__)
- `parte_comestivel_manual`
- `frutificacao_manual`
- `colheita_manual`
- Fill precedence:
1. scientifically validated local data;
2. location data already confirmed by internal flow;
3. given user manual;
4. automatic enrichment by integrations;
5. not informed.

## 2. Image submission
- The point needs `foto` to trigger scientific inference.
- File validations are applied on the inference endpoint.

## 3. AI Inference
- Endpoint: `POST /api/cientifico/pontos/<id>/inferencia/`.
- Result persisted in `PredicaoIA` with:
- provider,
- `predicoes_top_k`,
- `score_confianca`,
- `faixa_risco`,
- `requer_revisao_humana`.
- Updates suggestion at point (`nome_popular_sugerido`, `nome_cientifico_sugerido`, `score_identificacao`).

## 4. Review queue
- Endpoint: `GET /api/cientifico/revisao/fila/`.
- Access restricted to reviewer/admin.
- Filters: confidence range, status and day window.

## 5. Human review and validation
- Endpoint: `POST /api/cientifico/pontos/<id>/validacao/`.
- Registration in `ValidacaoEspecialista`.
- Update the point to `validado`, `rejeitado` or `necessita_revisao`.

## 6. AI vs human divergence
- Divergence justification field: `motivo_divergencia`.
- Allows recording the final species chosen by the specialist.

## 7. Auditable history
- Events are in `HistoricoValidacao` (`predicao_ia_gerada`, `validacao_humana`, etc.).
- Endpoint: `GET /api/cientifico/pontos/<id>/historico/`.
- Point enrichment also records:
- `payload_resumido_validacao.campos_fontes`
- `payload_resumido_validacao.divergencias_campos_locais`
- `payload_resumido_validacao.ambiguidade_taxonomica`
- `validacao_pendente_revisao_humana` when there is taxonomic conflict, low confidence or multiple plausible scientific names.

## 10. Auto-enrichment rules (cadastro/edição)
- Priority search:
1. `nome_cientifico` validated/submitted;
2. suggested scientific name;
3. fallback by popular name (local base) when necessary.
- Integrations attempted in the pipeline: Global Names, Tropicos, GBIF, iNaturalist, Trefle and Wikipedia/Wikimedia (short target fields).
- Without sufficient evidence, the food fields remain as "Not informed" (without inferring "No" due to lack of data).
- The common UI does not display the technical state `status_enriquecimento=pendente`; this state remains internal to audit/admin.

## 8. Scientific metrics
- Endpoint: `GET /api/cientifico/dashboard/`.
- Indicators: validation/rejection rate, AI-expert agreement, average validation time, distribution by confidence.

## 9. Territorial prioritization
- `calcular_score_prioridade(...)` service combines incidence, climate, reliability and recency.
- Result used in the dashboard as an operational sample.
