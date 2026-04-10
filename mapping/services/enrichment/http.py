import logging
import time
from dataclasses import dataclass
from typing import Any
from json import JSONDecodeError

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


@dataclass
class HTTPConfig:
    base_url: str
    timeout_seconds: float = 8.0
    retries: int = 2
    circuit_failures_threshold: int = 3
    circuit_open_seconds: int = 30


class ResilientHTTPClient:
    _circuit_registry: dict[str, dict[str, Any]] = {}

    def __init__(self, config: HTTPConfig):
        self.config = config
        self.session = requests.Session()
        retry_kwargs = {
            "total": config.retries,
            "read": config.retries,
            "connect": config.retries,
            "status_forcelist": [429, 500, 502, 503, 504],
            "backoff_factor": 0.4,
        }
        try:
            retry = Retry(allowed_methods=["GET"], **retry_kwargs)
        except TypeError:
            retry = Retry(method_whitelist=["GET"], **retry_kwargs)
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def _circuit_key(self) -> str:
        return self.config.base_url

    def _is_open(self) -> bool:
        state = self._circuit_registry.get(self._circuit_key()) or {}
        opened_at = state.get("opened_at")
        if not opened_at:
            return False
        if time.time() - opened_at > self.config.circuit_open_seconds:
            self._circuit_registry[self._circuit_key()] = {"failures": 0}
            return False
        return True

    def _register_failure(self):
        state = self._circuit_registry.setdefault(self._circuit_key(), {"failures": 0})
        state["failures"] = state.get("failures", 0) + 1
        if state["failures"] >= self.config.circuit_failures_threshold:
            state["opened_at"] = time.time()

    def _register_success(self):
        self._circuit_registry[self._circuit_key()] = {"failures": 0}

    @staticmethod
    def _mask_headers(headers: dict[str, Any]) -> dict[str, Any]:
        masked: dict[str, Any] = {}
        for key, value in (headers or {}).items():
            low = str(key).lower()
            if any(token in low for token in ("authorization", "token", "apikey", "api-key", "key", "secret", "password", "cookie")):
                masked[key] = "***"
            else:
                masked[key] = value
        return masked

    @staticmethod
    def _mask_params(params: dict[str, Any]) -> dict[str, Any]:
        masked: dict[str, Any] = {}
        for key, value in (params or {}).items():
            low = str(key).lower()
            if any(token in low for token in ("token", "apikey", "api_key", "key", "secret", "password")):
                masked[key] = "***"
            else:
                masked[key] = value
        return masked

    @staticmethod
    def _classify_http_error(status_code: int | None) -> str:
        if status_code is None:
            return "endpoint_error"
        if status_code == 401:
            return "auth_error"
        if status_code == 403:
            return "forbidden"
        if status_code == 404:
            return "not_found"
        if status_code == 429:
            return "rate_limit"
        if status_code in {502, 503, 504}:
            return "service_unavailable"
        if status_code >= 500:
            return "endpoint_error"
        return "http_error"

    @staticmethod
    def _response_excerpt(text: str | None, max_chars: int = 350) -> str:
        if not text:
            return ""
        compact = " ".join(str(text).split())
        return compact[:max_chars]

    @staticmethod
    def _response_summary(payload: Any) -> str:
        if isinstance(payload, dict):
            return f"json:dict keys={list(payload.keys())[:6]}"
        if isinstance(payload, list):
            return f"json:list len={len(payload)}"
        return f"json:{type(payload).__name__}"

    def get_json_detailed(self, path: str, *, params: dict[str, Any] | None = None, headers: dict[str, Any] | None = None) -> dict[str, Any]:
        if self._is_open():
            return {
                "payload": {},
                "error": "circuit_open",
                "error_type": "service_unavailable",
                "status_code": None,
                "latency_ms": 0,
                "url": f"{self.config.base_url}{path}",
                "method": "GET",
                "query_params": self._mask_params(params or {}),
                "request_headers": self._mask_headers(headers or {}),
            }

        url = f"{self.config.base_url}{path}"
        req_headers = {"User-Agent": "ColaboraPANC/1.0"}
        if headers:
            req_headers.update(headers)
        filtered_params = {k: v for k, v in (params or {}).items() if v not in (None, "")}

        started = time.perf_counter()
        try:
            response = self.session.get(
                url,
                params=filtered_params,
                timeout=self.config.timeout_seconds,
                headers=req_headers,
            )
            latency_ms = int((time.perf_counter() - started) * 1000)
            response.raise_for_status()
            payload = response.json()
            self._register_success()
            return {
                "payload": payload,
                "error": None,
                "error_type": None,
                "status_code": response.status_code,
                "latency_ms": latency_ms,
                "url": url,
                "method": "GET",
                "query_params": self._mask_params(filtered_params),
                "request_headers": self._mask_headers(req_headers),
                "response_summary": self._response_summary(payload),
            }
        except requests.Timeout as exc:
            self._register_failure()
            latency_ms = int((time.perf_counter() - started) * 1000)
            return {
                "payload": {},
                "error": str(exc),
                "error_type": "timeout",
                "status_code": None,
                "latency_ms": latency_ms,
                "url": url,
                "method": "GET",
                "query_params": self._mask_params(filtered_params),
                "request_headers": self._mask_headers(req_headers),
                "response_summary": "timeout",
                "response_excerpt": "",
            }
        except requests.ConnectionError as exc:
            self._register_failure()
            latency_ms = int((time.perf_counter() - started) * 1000)
            return {
                "payload": {},
                "error": str(exc),
                "error_type": "connection_error",
                "status_code": None,
                "latency_ms": latency_ms,
                "url": url,
                "method": "GET",
                "query_params": self._mask_params(filtered_params),
                "request_headers": self._mask_headers(req_headers),
                "response_summary": "connection_error",
                "response_excerpt": "",
            }
        except requests.HTTPError as exc:
            self._register_failure()
            latency_ms = int((time.perf_counter() - started) * 1000)
            status_code = exc.response.status_code if exc.response is not None else None
            body_excerpt = (exc.response.text[:350] if exc.response is not None and exc.response.text else "")
            return {
                "payload": {},
                "error": str(exc),
                "error_type": self._classify_http_error(status_code),
                "status_code": status_code,
                "latency_ms": latency_ms,
                "url": url,
                "method": "GET",
                "query_params": self._mask_params(filtered_params),
                "request_headers": self._mask_headers(req_headers),
                "response_summary": f"http_error:{status_code}",
                "response_excerpt": self._response_excerpt(body_excerpt),
            }
        except JSONDecodeError as exc:
            self._register_failure()
            latency_ms = int((time.perf_counter() - started) * 1000)
            return {
                "payload": {},
                "error": str(exc),
                "error_type": "parse_error",
                "status_code": None,
                "latency_ms": latency_ms,
                "url": url,
                "method": "GET",
                "query_params": self._mask_params(filtered_params),
                "request_headers": self._mask_headers(req_headers),
                "response_summary": "parse_error",
                "response_excerpt": "",
            }
        except Exception as exc:
            self._register_failure()
            latency_ms = int((time.perf_counter() - started) * 1000)
            logger.warning("Falha HTTP %s: %s", url, exc)
            return {
                "payload": {},
                "error": str(exc),
                "error_type": "erro_inesperado",
                "status_code": None,
                "latency_ms": latency_ms,
                "url": url,
                "method": "GET",
                "query_params": self._mask_params(filtered_params),
                "request_headers": self._mask_headers(req_headers),
                "response_summary": "unexpected_error",
                "response_excerpt": "",
            }

    def post_json_detailed(self, path: str, *, json_body: dict[str, Any] | None = None, headers: dict[str, Any] | None = None) -> dict[str, Any]:
        if self._is_open():
            return {
                "payload": {},
                "error": "circuit_open",
                "error_type": "service_unavailable",
                "status_code": None,
                "latency_ms": 0,
                "url": f"{self.config.base_url}{path}",
                "method": "POST",
                "request_headers": self._mask_headers(headers or {}),
                "response_summary": "circuit_open",
                "response_excerpt": "",
            }

        url = f"{self.config.base_url}{path}"
        req_headers = {"User-Agent": "ColaboraPANC/1.0", "Content-Type": "application/json"}
        if headers:
            req_headers.update(headers)

        started = time.perf_counter()
        try:
            response = self.session.post(
                url,
                json=json_body or {},
                timeout=self.config.timeout_seconds,
                headers=req_headers,
            )
            latency_ms = int((time.perf_counter() - started) * 1000)
            response.raise_for_status()
            payload = response.json()
            self._register_success()
            return {
                "payload": payload,
                "error": None,
                "error_type": None,
                "status_code": response.status_code,
                "latency_ms": latency_ms,
                "url": url,
                "method": "POST",
                "request_headers": self._mask_headers(req_headers),
                "response_summary": self._response_summary(payload),
                "response_excerpt": self._response_excerpt(response.text),
            }
        except requests.Timeout as exc:
            self._register_failure()
            latency_ms = int((time.perf_counter() - started) * 1000)
            return {
                "payload": {},
                "error": str(exc),
                "error_type": "timeout",
                "status_code": None,
                "latency_ms": latency_ms,
                "method": "POST",
                "url": url,
                "request_headers": self._mask_headers(req_headers),
                "response_summary": "timeout",
                "response_excerpt": "",
            }
        except requests.ConnectionError as exc:
            self._register_failure()
            latency_ms = int((time.perf_counter() - started) * 1000)
            return {
                "payload": {},
                "error": str(exc),
                "error_type": "connection_error",
                "status_code": None,
                "latency_ms": latency_ms,
                "method": "POST",
                "url": url,
                "request_headers": self._mask_headers(req_headers),
                "response_summary": "connection_error",
                "response_excerpt": "",
            }
        except requests.HTTPError as exc:
            self._register_failure()
            latency_ms = int((time.perf_counter() - started) * 1000)
            status_code = exc.response.status_code if exc.response is not None else None
            return {
                "payload": {},
                "error": str(exc),
                "error_type": self._classify_http_error(status_code),
                "status_code": status_code,
                "latency_ms": latency_ms,
                "method": "POST",
                "url": url,
                "request_headers": self._mask_headers(req_headers),
                "response_summary": f"http_error:{status_code}",
                "response_excerpt": self._response_excerpt(exc.response.text if exc.response is not None else ""),
            }
        except JSONDecodeError as exc:
            self._register_failure()
            latency_ms = int((time.perf_counter() - started) * 1000)
            return {
                "payload": {},
                "error": str(exc),
                "error_type": "parse_error",
                "status_code": None,
                "latency_ms": latency_ms,
                "method": "POST",
                "url": url,
                "request_headers": self._mask_headers(req_headers),
                "response_summary": "parse_error",
                "response_excerpt": "",
            }
        except Exception as exc:
            self._register_failure()
            latency_ms = int((time.perf_counter() - started) * 1000)
            return {
                "payload": {},
                "error": str(exc),
                "error_type": "erro_inesperado",
                "status_code": None,
                "latency_ms": latency_ms,
                "method": "POST",
                "url": url,
                "request_headers": self._mask_headers(req_headers),
                "response_summary": "unexpected_error",
                "response_excerpt": "",
            }

    def get_json(self, path: str, *, params: dict[str, Any] | None = None) -> tuple[dict[str, Any] | list, str | None]:
        detailed = self.get_json_detailed(path, params=params)
        return detailed.get("payload", {}), detailed.get("error")

    def get_text_detailed(self, path: str, *, params: dict[str, Any] | None = None, headers: dict[str, Any] | None = None) -> dict[str, Any]:
        if self._is_open():
            return {"payload": "", "error": "circuit_open", "error_type": "service_unavailable", "status_code": None, "latency_ms": 0}

        url = f"{self.config.base_url}{path}"
        req_headers = {"User-Agent": "ColaboraPANC/1.0"}
        if headers:
            req_headers.update(headers)
        filtered_params = {k: v for k, v in (params or {}).items() if v not in (None, "")}
        started = time.perf_counter()
        try:
            response = self.session.get(url, params=filtered_params, timeout=self.config.timeout_seconds, headers=req_headers)
            latency_ms = int((time.perf_counter() - started) * 1000)
            response.raise_for_status()
            self._register_success()
            return {
                "payload": response.text or "",
                "error": None,
                "error_type": None,
                "status_code": response.status_code,
                "latency_ms": latency_ms,
                "url": url,
                "method": "GET",
                "query_params": self._mask_params(filtered_params),
                "request_headers": self._mask_headers(req_headers),
                "content_type": response.headers.get("Content-Type", ""),
            }
        except requests.Timeout as exc:
            self._register_failure()
            return {"payload": "", "error": str(exc), "error_type": "timeout", "status_code": None}
        except requests.ConnectionError as exc:
            self._register_failure()
            return {"payload": "", "error": str(exc), "error_type": "connection_error", "status_code": None}
        except requests.HTTPError as exc:
            self._register_failure()
            status_code = exc.response.status_code if exc.response is not None else None
            return {
                "payload": exc.response.text if exc.response is not None else "",
                "error": str(exc),
                "error_type": self._classify_http_error(status_code),
                "status_code": status_code,
            }
        except Exception as exc:
            self._register_failure()
            return {"payload": "", "error": str(exc), "error_type": "erro_inesperado", "status_code": None}
