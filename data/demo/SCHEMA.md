# Proposed Demo Schema (Draft)

Status: structural draft only (no fabricated scientific records).

## Suggested fields for a minimal point record

- `id` (string or integer)
- `latitude` (decimal)
- `longitude` (decimal)
- `observed_at` (ISO date or datetime)
- `vernacular_name` (string)
- `scientific_name` (string, optional)
- `validation_status` (enum: pending/reviewed/validated/rejected)
- `source` (enum/string)

## Validation notes

- Field names and constraints must match implementation before public release.
- Sensitive or personal fields must be excluded from public demo bundles.
