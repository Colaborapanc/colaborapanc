from unittest.mock import Mock

from django.contrib.gis.geos import Point
from django.test import TestCase, override_settings

from mapping.models import PontoPANC, PlantaReferencial
from mapping.services.enrichment.field_extractors import (
    extract_colheita,
    extract_comestivel,
    extract_frutificacao,
    extract_parte_comestivel,
)
from mapping.services.enrichment.planta_enrichment_pipeline import PlantaEnrichmentPipeline
from mapping.services.enrichment.wikipedia_enrichment_service import WikipediaEnrichmentService
from mapping.services.external.wikimedia_client import WikimediaClient


class FieldExtractorTests(TestCase):
    def test_extract_each_target_field(self):
        text = (
            "A planta é comestível. As folhas e frutos são comestíveis. "
            "A frutificação ocorre entre março e junho. A colheita principal ocorre em maio e junho."
        )
        self.assertEqual(extract_comestivel(text).value, "Sim")
        self.assertEqual(extract_parte_comestivel(text).value, "folha, fruto")
        self.assertEqual(extract_frutificacao(text).value, "mar, jun")
        self.assertIn("mai", extract_colheita(text).value)


class WikipediaResolutionTests(TestCase):
    def setUp(self):
        self.service = WikipediaEnrichmentService()

    def test_resolution_fallback_scientific_to_popular(self):
        self.service.client.search_page_candidates = Mock(side_effect=[([], None), ([{"title": "Ora-pro-nóbis", "snippet": "Espécie de planta"}], None)])
        resolved = self.service.resolve_page(scientific_valid="Nome Inexistente", scientific_suggested=None, popular_name="Ora-pro-nóbis")
        self.assertTrue(resolved["ok"])
        self.assertEqual(resolved["page"].title, "Ora-pro-nóbis")

    def test_insufficient_content_does_not_fill(self):
        self.service.resolve_page = Mock(return_value={"ok": True, "page": Mock(title="Teste", language="pt", confidence=0.9), "attempts": []})
        self.service.client.fetch_page_extract = Mock(return_value=({"extract": ""}, None))
        result = self.service.enrich_target_fields(scientific_valid="Poa annua", scientific_suggested=None, popular_name="Capim")
        self.assertFalse(result["ok"])
        self.assertEqual(result["error_type"], "insufficient_content")

    def test_timeout_handling(self):
        self.service.resolve_page = Mock(return_value={"ok": True, "page": Mock(title="Teste", language="pt", confidence=0.9), "attempts": []})
        self.service.client.fetch_page_extract = Mock(return_value=({}, "Read timed out"))
        result = self.service.enrich_target_fields(scientific_valid="Poa annua", scientific_suggested=None, popular_name="Capim")
        self.assertFalse(result["ok"])
        self.assertEqual(result["error_type"], "timeout")


class WikimediaClientCacheTests(TestCase):
    @override_settings(
        WIKIMEDIA_USER_AGENT="ColaboraPANC/1.0 (Warleyalisson; warleyalisson@gmail.com)",
        WIKIMEDIA_API_USER_AGENT="ColaboraPANC/1.0 (Warleyalisson; warleyalisson@gmail.com)",
    )
    def test_cache_reuses_search_response(self):
        client = WikimediaClient()

        class _FakeHttp:
            def __init__(self):
                self.calls = 0
                self.session = Mock()

            def get_json(self, path, params=None):
                self.calls += 1
                return ({"query": {"search": [{"title": "Pereskia aculeata", "snippet": "Espécie de planta"}]}}, None)

        fake = _FakeHttp()
        client.clients["pt"] = fake
        client.search_page_candidates(query="Pereskia aculeata", language="pt", limit=2)
        client.search_page_candidates(query="Pereskia aculeata", language="pt", limit=2)
        self.assertEqual(fake.calls, 1)


class WikipediaPipelineCompatibilityTests(TestCase):
    def setUp(self):
        self.planta = PlantaReferencial.objects.create(nome_popular="Capim", nome_cientifico="Poa annua")
        self.ponto = PontoPANC.objects.create(
            planta=self.planta,
            nome_popular="Capim",
            localizacao=Point(-46.63, -23.55, srid=4326),
            latitude=-23.55,
            longitude=-46.63,
            comestibilidade_status="sim",
            comestibilidade_confirmada=True,
        )

    def test_local_validated_data_has_precedence(self):
        pipeline = PlantaEnrichmentPipeline()
        pipeline.gnv.validate_name = Mock(return_value={"ok": True, "nome_cientifico_validado": "Poa annua", "nome_aceito": "Poa annua", "autoria": "L."})
        pipeline.tropicos.resolve = Mock(return_value={"ok": True, "nome_aceito": "Poa annua", "autoria": "L.", "sinonimos": []})
        pipeline.gbif.fetch = Mock(return_value={"ok": True, "ocorrencias_gbif": 20, "distribuicao_resumida": "Plantae"})
        pipeline.inat.fetch = Mock(return_value={"ok": False, "error": "timeout"})
        pipeline.trefle.fetch_optional_traits = Mock(return_value={"ok": False, "error": "not_found"})
        pipeline.wikipedia.enrich_target_fields = Mock(
            return_value={
                "ok": True,
                "status": "ok",
                "source": {"fonte": "wikimedia", "titulo": "Poa annua", "idioma": "pt", "confianca": 0.9},
                "fields": {
                    "comestivel": {"value": "Não", "confirmed": True, "evidence": "texto"},
                    "parte_comestivel": {"value": "folha", "confirmed": True, "evidence": "texto"},
                    "frutificacao": {"value": "mar, abr", "confirmed": True, "evidence": "texto"},
                    "colheita": {"value": "mai", "confirmed": True, "evidence": "texto"},
                },
                "attempts": [],
            }
        )

        result = pipeline.run_for_ponto(self.ponto, include_trefle=False, origem="teste")
        self.ponto.refresh_from_db()

        self.assertTrue(result["ok"])
        self.assertEqual(self.ponto.comestibilidade_status, "sim")
        self.assertTrue(self.ponto.comestibilidade_confirmada)
        self.assertIn("divergencias_campos_locais", self.ponto.payload_resumido_validacao)
        self.assertIn("wikipedia", self.ponto.payload_resumido_validacao)

    def test_ausencia_de_evidencia_nao_gera_falso_nao(self):
        self.ponto.comestibilidade_confirmada = False
        self.ponto.comestibilidade_status = "indeterminado"
        self.ponto.save(update_fields=["comestibilidade_confirmada", "comestibilidade_status"])

        pipeline = PlantaEnrichmentPipeline()
        pipeline.gnv.validate_name = Mock(return_value={"ok": True, "nome_cientifico_validado": "Poa annua"})
        pipeline.tropicos.resolve = Mock(return_value={"ok": True, "nome_aceito": "Poa annua"})
        pipeline.gbif.fetch = Mock(return_value={"ok": True, "ocorrencias_gbif": 10})
        pipeline.inat.fetch = Mock(return_value={"ok": False, "error": "not_found"})
        pipeline.trefle.fetch_optional_traits = Mock(return_value={"ok": False, "error": "not_found"})
        pipeline.wikipedia.enrich_target_fields = Mock(
            return_value={
                "ok": True,
                "status": "ok",
                "source": {"fonte": "wikimedia", "titulo": "Poa annua", "idioma": "pt", "confianca": 0.9},
                "fields": {
                    "comestivel": {"value": "Não informado", "confirmed": False, "evidence": "conteúdo insuficiente"},
                    "parte_comestivel": {"value": "Não informado", "confirmed": False, "evidence": "conteúdo insuficiente"},
                    "frutificacao": {"value": "Não informado", "confirmed": False, "evidence": "conteúdo insuficiente"},
                    "colheita": {"value": "Não informado", "confirmed": False, "evidence": "conteúdo insuficiente"},
                },
                "attempts": [],
            }
        )

        pipeline.run_for_ponto(self.ponto, include_trefle=False, origem="teste")
        self.ponto.refresh_from_db()

        self.assertEqual(self.ponto.comestibilidade_status, "indeterminado")
        self.assertFalse(self.ponto.comestibilidade_confirmada)
