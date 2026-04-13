# Troubleshooting (Legacy Technical Annex)

## Status

**Rewritten and maintained as active technical annex.**

## Scope

Quick operational troubleshooting for common setup/runtime issues not fully covered in canonical user/admin summaries.

## Common scenarios

### 1) Mobile cannot sync pending offline records
- Check network restoration and API base URL.
- Confirm backend is reachable and authenticated session/token is valid.
- Retry sync and inspect pending queue status in app.

### 2) Integration appears offline/degraded
- Use admin integration panel and retest endpoint.
- Check missing env vars/credentials first.
- Distinguish auth/config errors from upstream outages/timeouts.

### 3) AI result seems inconsistent
- Treat output as assistive; verify review status.
- Check whether human validation is still pending.
- Review confidence context before acting on result.

### 4) Deployment/runtime mismatch
- Re-check installation/deployment canonical guides.
- Validate environment variables and secrets.
- Confirm production-safe settings (`DEBUG=False`, strict CORS in production).

## Canonical references

- User flow: `docs/en/user-guide.md`
- Contributor flow: `docs/en/contributing.md`
- Admin operation: `docs/en/admin.md`
- Installation/deployment: `docs/en/installation.md`, `docs/en/deployment.md`
