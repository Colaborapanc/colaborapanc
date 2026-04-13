from django.test import SimpleTestCase
from unittest.mock import patch

from mapping.services.environment.mapbiomas import MapBiomasService
from mapping.services.ia_identificacao.plantid_health import PlantIdHealthService
from mapping.services.taxonomy.global_names import GlobalNamesService
from mapping.services.weather.inmet import INMETService


class TestGlobalNamesParser(SimpleTestCase):
    def test_extract_best_candidate_accepts_verifications_schema(self):
        payload = {
            "data": [
                {
                    "bestResult": {
                        "canonicalName": "Poa annua",
                        "currentName": "Poa annua",
                    }
                }
            ]
        }
        best, error = GlobalNamesService._extract_best_candidate(payload)
        self.assertEqual(error, None)
        self.assertEqual(best.get("canonicalName"), "Poa annua")


class TestMapBiomasHealth(SimpleTestCase):
    @patch("mapping.services.environment.mapbiomas.MapBiomasService._graphql_health_query")
    def test_healthcheck_returns_structured_payload(self, mocked_query):
        mocked_query.return_value = {
            "ok": False,
            "error": "graphql_error",
            "error_type": "schema_error",
            "method": "POST",
            "status_code": 200,
            "response_summary": "json:dict",
            "response_excerpt": '{"errors":[...]}',
            "latency_ms": 123,
        }
        service = MapBiomasService()
        service.email = "foo@bar.com"
        service.password = "secret"
        result = service.healthcheck()
        self.assertFalse(result["ok"])
        self.assertEqual(result["error_type"], "schema_error")
        self.assertEqual(result["method"], "POST")


class TestPlantIdHealth(SimpleTestCase):
    def test_missing_key_returns_not_configured(self):
        service = PlantIdHealthService()
        service.api_key = ""
        result = service.healthcheck()
        self.assertFalse(result["ok"])
        self.assertEqual(result["error_type"], "credencial_ausente")
        self.assertEqual(result["method"], "CHECK")
        self.assertTrue(result["endpoint"].endswith("/identify"))

    def test_health_check_is_limited_and_never_online_without_real_identification(self):
        service = PlantIdHealthService()
        service.api_key = "x"
        result = service.healthcheck()
        self.assertFalse(result["ok"])
        self.assertEqual(result["error_type"], "verificacao_limitada")
        self.assertEqual(result["response_summary"], "verificacao_limitada")
        self.assertEqual(result["method"], "CHECK")
        self.assertIn("nenhuma chamada externa", result["response_excerpt"])
        self.assertTrue(result["endpoint"].endswith("/identify"))


class TestInmetEndpoint(SimpleTestCase):
    def test_inmet_default_endpoint_uses_current_base_url(self):
        service = INMETService()
        self.assertEqual(service.endpoint, "https://apiprevmet3.inmet.gov.br/")
