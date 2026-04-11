# Release Preparation Plan (v1.0.0 Draft)

This checklist prepares a formal release without performing external publication steps from this repository-only workflow.

## Release checklist

- [ ] Confirm final version identifier and tag (e.g., `v1.0.0`).
- [ ] Confirm `CHANGELOG.md` entries for the release.
- [ ] Validate README + docs links.
- [ ] Validate tests in the target release environment.
- [ ] Create GitHub Release notes.
- [ ] Attach release assets (if any).
- [ ] Archive in external service (e.g., Zenodo) for DOI/PID.
- [ ] Update `CITATION.cff` and `codemeta.json` with final DOI/PID.

## External dependencies

The following actions must be executed manually by maintainers/authors:

1. GitHub tag and public release publication.
2. DOI/PID archival registration.
3. Final metadata confirmation (authors, affiliations, ORCID, corresponding e-mail).
