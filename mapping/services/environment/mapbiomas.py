import os
from django.conf import settings
from django.core.cache import cache

from mapping.services.enrichment.http import HTTPConfig, ResilientHTTPClient


class MapBiomasService:
    name = "MapBiomas"
    requires_token = True

    def __init__(self):
        self.base_url = (
            getattr(settings, "MAPBIOMAS_API_URL", "")
            or os.environ.get("MAPBIOMAS_API_URL", "https://plataforma.alerta.mapbiomas.org/api/v2/graphql")
        ).rstrip("/")
        self.email = (getattr(settings, "MAPBIOMAS_EMAIL", "") or os.environ.get("MAPBIOMAS_EMAIL", "")).strip()
        self.password = (getattr(settings, "MAPBIOMAS_PASSWORD", "") or os.environ.get("MAPBIOMAS_PASSWORD", "")).strip()
        self.auth_client = ResilientHTTPClient(HTTPConfig(base_url=self.base_url, timeout_seconds=6, retries=0))
        self.query_client = ResilientHTTPClient(HTTPConfig(base_url=self.base_url, timeout_seconds=4.5, retries=0))
        self._token: str | None = None
        self._cache_key = "mapbiomas_health_token"

    def _authenticate(self) -> dict:
        cached_token = cache.get(self._cache_key)
        if cached_token:
            self._token = cached_token
            return {"ok": True, "token": cached_token, "method": "POST", "status_code": 200, "endpoint": self.base_url, "response_summary": "cached_token"}

        mutation = """
        mutation SignIn($email: String!, $password: String!) {
          signIn(email: $email, password: $password) { token }
        }
        """
        req = self.auth_client.post_json_detailed(
            "",
            json_body={"query": mutation, "variables": {"email": self.email, "password": self.password}},
        )
        payload = req.get("payload") if isinstance(req.get("payload"), dict) else {}
        sign_in = ((payload.get("data") or {}).get("signIn") or {}) if payload else {}
        token = sign_in.get("token")
        if token:
            self._token = token
            cache.set(self._cache_key, token, 60 * 15)
            return {**req, "ok": True, "token": token}
        return {**req, "ok": False, "error": req.get("error") or "auth_error", "error_type": req.get("error_type") or "auth_error"}

    def _graphql_health_query(self) -> dict:
        if not self._token:
            auth = self._authenticate()
            if not auth.get("ok"):
                return auth
        query = "query HealthCheck { __typename }"
        req = self.query_client.post_json_detailed(
            "",
            json_body={"query": query},
            headers={"Authorization": f"Bearer {self._token}"},
        )
        payload = req.get("payload") if isinstance(req.get("payload"), dict) else {}
        has_data = isinstance(payload.get("data"), dict) and bool(payload.get("data"))
        has_errors = bool(payload.get("errors"))
        if req.get("status_code") in (401, 403):
            cache.delete(self._cache_key)
            self._token = None
        return {
            **req,
            "ok": bool(has_data and not has_errors and not req.get("error")),
            "error": req.get("error") or ("graphql_error" if has_errors else None) or ("response_empty" if not has_data else None),
            "error_type": req.get("error_type") or ("schema_error" if has_errors else None) or ("response_empty" if not has_data else None),
        }

    def healthcheck(self):
        if not self.email or not self.password:
            return {"ok": False, "error": "missing_credentials", "error_type": "credencial_ausente", "endpoint": self.base_url, "method": "POST"}

        result = self._graphql_health_query()
        return {
            "ok": bool(result.get("ok")),
            "error": result.get("error"),
            "error_type": result.get("error_type"),
            "endpoint": self.base_url,
            "method": result.get("method", "POST"),
            "status_code": result.get("status_code"),
            "response_summary": result.get("response_summary"),
            "response_excerpt": result.get("response_excerpt"),
            "latency_ms": result.get("latency_ms"),
        }
