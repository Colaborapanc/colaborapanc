# Editorial `src/` Layout Note

This repository historically organizes implementation code primarily under:

- `mapping/` (main Django app and domain services)
- `config/` (Django project settings and routing)
- `mobile/` (React Native/Expo app)

The `src/` directory is intentionally added as a **non-destructive editorial layer** to align with software publication expectations where reviewers often look for a `src` anchor.

## Important

- No runtime code paths were moved into this folder.
- Existing imports, scripts, and execution commands remain unchanged.
- See `docs/en/project_structure.md` for the full repository map.
