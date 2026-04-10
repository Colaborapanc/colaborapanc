import os
import xml.etree.ElementTree as ET

from mapping.services.enrichment.http import HTTPConfig, ResilientHTTPClient


class INMETService:
    name = "INMET"
    requires_token = False

    def __init__(self):
        self.endpoint = os.environ.get("INMET_RSS_URL", "https://apiprevmet3.inmet.gov.br/")
        self.fallback_endpoints = [self.endpoint]

    def healthcheck(self):
        last_error = None
        for endpoint in self.fallback_endpoints:
            client = ResilientHTTPClient(HTTPConfig(base_url=endpoint.rstrip("/"), timeout_seconds=6, retries=1))
            response = client.get_text_detailed("", params={})
            text = (response.get("payload") or "").strip()
            if response.get("error"):
                last_error = {
                    "ok": False,
                    "error": response.get("error"),
                    "error_type": response.get("error_type"),
                    "endpoint": endpoint,
                    "status_code": response.get("status_code"),
                }
                return last_error

            if not text:
                last_error = {"ok": False, "error": "empty_response", "error_type": "response_empty", "endpoint": endpoint}
                continue

            if text.startswith("<"):
                try:
                    root = ET.fromstring(text)
                    items = root.findall(".//item")
                    return {
                        "ok": True,
                        "error": None,
                        "error_type": None,
                        "endpoint": endpoint,
                        "result_summary": f"rss_items={len(items)}",
                    }
                except Exception as exc:
                    last_error = {"ok": False, "error": f"invalid_rss:{exc}", "error_type": "parse_error", "endpoint": endpoint}
                    continue

            # fallback para resposta HTML de página de status
            return {
                "ok": True,
                "error": None,
                "error_type": None,
                "endpoint": endpoint,
                "result_summary": "html_status_page",
            }
        return last_error or {"ok": False, "error": "inmet_unavailable", "error_type": "service_unavailable", "endpoint": self.endpoint}
