# Security Policy — ColaboraPANC

## Supported Versions

| Version | Supported |
|---------|-----------|
| Latest on `main` | Yes |
| Older branches | No |

## Reporting a Vulnerability

**Do not open a public GitHub issue for security vulnerabilities.**

If you discover a potential security issue in ColaboraPANC, please report it privately:

1. Send an email to the project maintainers (contact via the repository owner's GitHub profile).
2. Include in your report:
   - A clear description of the issue.
   - Steps to reproduce (if applicable).
   - Potential impact assessment.
   - Any suggested mitigation (optional).
3. You will receive an acknowledgement within 5 business days.
4. We aim to release a fix within 30 days of confirmation.

We will credit reporters in the release notes unless you request anonymity.

## Known Security Considerations

- **External API keys:** All keys for PlantNet, Plant.id, MapBiomas, NASA FIRMS, and other services must be stored in `.env` (never committed). The `.env.example` file contains only placeholder values.
- **Secret key:** Django's `SECRET_KEY` must be unique per deployment and never shared.
- **CORS:** Production deployments must configure `CORS_ALLOWED_ORIGINS` as a strict whitelist (see `.env.example`).
- **Database credentials:** PostgreSQL credentials must be environment-variable-driven, not hardcoded.
- **Debug mode:** `DEBUG=False` is mandatory in production.
- **Admin credentials:** Default admin credentials (`admin / admin123`) provided in `SETUP.md` are for local development only and must be changed before any public deployment.

## Scope

This policy covers the ColaboraPANC source code in this repository. It does not cover third-party services (PlantNet, Plant.id, MapBiomas, etc.) or infrastructure managed outside this repository.
