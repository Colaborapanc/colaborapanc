# Wikimedia/Wikipedia integration in controlled enrichment

## Objective
Add Wikimedia/Wikipedia as **complementary source** to fill in only 4 fields:
- Edible
- Edible part
- Fruiting
- Harvest

Without replacing the local scientific flow, without expanding to an encyclopedic profile and without polluting the interface.

## Architecture
Isolated layers:
1. **External HTTP Client**: `mapping/services/external/wikimedia_client.py`
2. **Target Field Extractors**: `mapping/services/enrichment/field_extractors.py`
3. **Wikimedia enrichment orchestration**: `mapping/services/enrichment/wikipedia_enrichment_service.py`
4. **Compatibility with current pipeline**: `mapping/services/enrichment/planta_enrichment_pipeline.py`

## Data precedence policy
1. Location data already confirmed (`*_confirmada=True`) always prevails.
2. Data consolidated by internal flow remains a priority.
3. Wikipedia/Wikimedia only fills in gaps with confirmed evidence.
4. Absence of evidence **doesn't** generate “No” for edibility.

When there is a divergence with a confirmed local value, the system:
- keeps the local value,
- records the divergence in `payload_resumido_validacao.divergencias_campos_locais`.

## Page resolution strategy
Order of attempt:
1. Validated scientific name
2. Suggested scientific name
3. Main popular name
4. Simple normalized variations

Language:
- Priority: `pt`
- Controlled fallback: `en`

Minimum validation:
- semantic adherence score,
- blocking ambiguous/disambiguation pages,
- low confidence rejection (`WIKIMEDIA_MIN_MATCH_CONFIDENCE`).

## Enriched fields and normalization
Normalized output for the pipeline:
- `comestibilidade_status`: `sim | nao | indeterminado`
- `parte_comestivel`: normalized short list
- `frutificacao_meses`: short list (`jan`..`dez`) when possible
- `colheita_periodo`: short list or short string

Fields without evidence remain unfilled.

## Traceability
For each run, the pipeline records:
- Wikimedia enrichment status,
- page title and language,
- correspondence confidence,
- summary attempts at resolution,
- evidence per extracted field,
- discrepancies with confirmed local data,
- classified error when it exists.

Everything is saved in the audit JSON (`payload_resumido_validacao`) without breaking the current schema.

## Caching and responsible use
- Cache per query (`search`) and per page (`extract`) with configurable TTL.
- Avoid repeated calls for the same titles/queries.
- Requests with timeout/retry and circuit breaker inherited from the resilient HTTP client.

## Mandatory customer identification
Configurations centered on `settings.py` and `.env`:
- `WIKIMEDIA_USER`
- `WIKIMEDIA_EMAIL`
- `WIKIMEDIA_USER_AGENT`
- `WIKIMEDIA_API_USER_AGENT`

Recommended format:
`ColaboraPANC/<versao> (Warleyalisson; warleyalisson@gmail.com)`

## Behavior in external unavailability
Errors are classified (timeout, rate limit, network, ambiguity, insufficient content, etc.) and:
- do not break registration/revalidation,
- do not expose gross errors to the end user,
- keep safe fallback (__CODE0__/não preenchido).

## Public UX (registration and details)
- The internal enrichment status `"pendente"` is not displayed for ordinary users.
- The public screen only shows useful data:
- confirmed values ​​for edibility/edible part/fruiting/harvesting;
- `Não informado` when there is not enough evidence.
- The technical status remains available only in the administrative block.

## Registration flow with autocomplete
- The **Popular name** field uses debounce and combines fonts:
1. validated local base;
2. local history of points;
3. external fallback (iNaturalist autocomplete) with cache.
- When choosing a suggestion with an exact match, the **Scientific name** is auto-populated.
- The source of the resolution is persisted in the operational payload (`payload_resumido_validacao.resolucao_nome`) without polluting the interface.

## Limitations
- Text extraction depends on linguistic standards (pt/en), and may not cover all page formats.
- On very short pages, the system may keep fields as uninformed for security reasons.
- Wikipedia is not a substitute for local scientific validation.
