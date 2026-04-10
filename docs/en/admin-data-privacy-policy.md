# Administrative Annex: Data and Privacy Policy (Technical)

## Scope

This annex separates data governance/privacy policy from day-to-day admin operations.

## 1) Data classes handled by platform operations
- Account/authentication data.
- Georeferenced observation data (location, report, image).
- AI inference and scientific validation metadata.
- Interaction data (messages, notifications, gamification).
- Integration/operations telemetry and logs.

## 2) Sensitive-context data
- Geolocation may expose environmentally sensitive areas.
- Images may include metadata/contextual traces.
- Operational logs can contain incident traces requiring controlled access.

## 3) Policy baseline (LGPD-aligned technical posture)
- Purpose limitation: process only for platform scientific/operational purpose.
- Data minimization: collect/store only necessary data.
- Transparency: disclose assistive AI limitations and human-review model.
- Access control: role-based access for admin/reviewer operations.
- Secret management: keep credentials outside code and rotate when needed.

## 4) Retention and minimization practices
- Keep scientific history for auditability and governance.
- Define retention windows by data class (account/image/log).
- Use reduced geospatial precision/anonymization in sensitive public contexts when policy requires it.

## 5) Privacy-aware operations checklist
1. Verify least-privilege access before export/administrative action.
2. Avoid unnecessary exposure of raw personal/location data in dashboards.
3. Ensure incident and audit logs are access-restricted.
4. Apply retention/deletion routines according to approved policy.
