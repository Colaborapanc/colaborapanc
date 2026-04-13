from types import SimpleNamespace
from unittest.mock import MagicMock, patch
import os

from allauth.socialaccount.models import SocialApp
from django.contrib.sites.models import Site
from django.test import RequestFactory, SimpleTestCase, TestCase, override_settings

from mapping.signals import sincronizar_incidentes_novo_ponto
from mapping.templatetags.socialaccount_extras import google_social_login_enabled
from mapping.services.traits.trefle import TrefleTraitsService
from mapping.services.integrations.healthcheck import IntegrationHealthcheckService
from mapping.services.integrations.status_utils import classify_error_type
from mapping.services.taxonomy.global_names import GlobalNamesService
from mapping.services.enrichment.search_terms import build_progressive_search_terms
from mapping.services.enrichment.planta_enrichment_pipeline import PlantaEnrichmentPipeline


class SinalSincronizacaoIncidentesTest(SimpleTestCase):
    @patch("mapping.signals.EnvironmentalMonitorService")
    @patch("mapping.signals.transaction.on_commit")
    def test_dispara_sincronizacao_ao_criar_ponto(self, on_commit_mock, monitor_service_mock):
        ponto = SimpleNamespace(id=123)

        def executar_imediatamente(callback):
            callback()

        on_commit_mock.side_effect = executar_imediatamente
        monitor_instance = monitor_service_mock.return_value
        monitor_instance.sync = MagicMock()

        sincronizar_incidentes_novo_ponto(
            sender=None,
            instance=ponto,
            created=True,
        )

        on_commit_mock.assert_called_once()
        monitor_instance.sync.assert_called_once_with(
            ponto_id=123,
            days=365,
            latest_only=True,
        )

    @patch("mapping.signals.EnvironmentalMonitorService")
    @patch("mapping.signals.transaction.on_commit")
    def test_nao_sincroniza_quando_nao_e_criacao(self, on_commit_mock, monitor_service_mock):
        ponto = SimpleNamespace(id=456)

        sincronizar_incidentes_novo_ponto(
            sender=None,
            instance=ponto,
            created=False,
        )

        on_commit_mock.assert_not_called()
        monitor_service_mock.assert_not_called()


class SocialLoginTemplateTagTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.request = self.factory.get("/accounts/login/")
        self.site = Site.objects.get_current()
        self.request.site = self.site

    def test_google_social_login_disabled_sem_social_app(self):
        enabled = google_social_login_enabled({"request": self.request})
        self.assertFalse(enabled)

    def test_google_social_login_enabled_com_social_app_configurada(self):
        app = SocialApp.objects.create(
            provider="google",
            name="Google",
            client_id="abc",
            secret="xyz",
        )
        app.sites.add(self.site)

        enabled = google_social_login_enabled({"request": self.request})
        self.assertTrue(enabled)


class TrefleTraitsServiceTests(SimpleTestCase):
    @patch("mapping.services.traits.trefle.EnrichmentCache")
    @patch("mapping.services.traits.trefle.ResilientHTTPClient")
    def test_fetch_optional_traits_handles_none_nested_objects(self, client_cls, cache_cls):
        os.environ["TREFLE_API_TOKEN"] = "token"
        cache = cache_cls.return_value
        cache.get.return_value = None

        client = client_cls.return_value
        client.get_json_detailed.side_effect = [
            {"payload": {"data": [{"id": 123}]}, "error": None, "error_type": None},
            {"payload": {"data": {"growth": None, "specifications": None, "images": None}}, "error": None, "error_type": None},
        ]

        service = TrefleTraitsService()
        result = service.fetch_optional_traits("Poa annua")
        self.assertTrue(result["ok"])
        self.assertEqual(result["fruit_months"], [])
        self.assertEqual(result["growth_months"], [])
        self.assertEqual(result["bloom_months"], [])
        self.assertEqual(result["edible_part"], [])


class IntegrationHealthcheckServiceTests(SimpleTestCase):
    @override_settings(WIKIMEDIA_USER="Warleyalisson", WIKIMEDIA_EMAIL="warleyalisson@gmail.com")
    def test_missing_env_considers_settings_defaults(self):
        service = IntegrationHealthcheckService()
        missing = service._missing_envs(["WIKIMEDIA_USER", "WIKIMEDIA_EMAIL"])
        self.assertEqual(missing, [])


class IntegrationStatusUtilsTests(SimpleTestCase):
    def test_classify_error_type_prefers_verificacao_limitada(self):
        error_type = classify_error_type(
            status_detail="parcial",
            error_message="verificacao_limitada",
            configured=True,
        )
        self.assertEqual(error_type, "verificacao_limitada")


class GlobalNamesServiceTests(SimpleTestCase):
    def test_extract_best_candidate_accepts_alt_schema(self):
        payload = {
            "verifications": [
                {
                    "canonicalName": "Poa annua",
                    "currentName": "Poa annua",
                    "authorship": "L.",
                }
            ]
        }
        best, error = GlobalNamesService._extract_best_candidate(payload)
        self.assertIsNone(error)
        self.assertEqual(best.get("canonicalName"), "Poa annua")


class EnrichmentSearchTermsTests(SimpleTestCase):
    def test_build_progressive_search_terms_expands_and_dedupes(self):
        terms = build_progressive_search_terms(
            submitted_scientific="Pereskia aculeata Mill.",
            validated_scientific="Pereskia aculeata",
            accepted_name="Pereskia aculeata",
            synonyms=["Cactaceae aculeata"],
            popular_names=["Ora-pro-nóbis", "ora pro nobis"],
            aliases=["Pereskia-aculeata"],
        )
        self.assertIn("Pereskia aculeata", terms)
        self.assertIn("Ora-pro-nóbis", terms)
        self.assertEqual(len(terms), len(set(t.lower() for t in terms)))


class PlantaEnrichmentPipelineLocalReuseTests(SimpleTestCase):
    def test_run_for_ponto_prioritizes_local_canonical(self):
        pipeline = PlantaEnrichmentPipeline()
        ponto = SimpleNamespace(
            id=1,
            planta_id=10,
            planta=SimpleNamespace(
                is_fully_enriched=True,
                nome_cientifico_submetido="Pereskia aculeata",
                nome_cientifico_validado="Pereskia aculeata",
                nome_aceito="Pereskia aculeata",
                sinonimos=["Peireskia aculeata"],
                autoria="Mill.",
                fontes_utilizadas=["GBIF", "Tropicos"],
                nivel_confianca_enriquecimento=0.9,
                distribuicao_resumida="América do Sul",
                imagem_url="https://example.com/img.jpg",
                imagem_fonte="GBIF",
                licenca_imagem="CC-BY",
            ),
            nome_cientifico_submetido="Pereskia aculeata",
            nome_cientifico_validado="",
            nome_aceito="",
            sinonimos=[],
            autoria="",
            status_enriquecimento="pendente",
            fontes_enriquecimento=[],
            integracoes_utilizadas=[],
            grau_confianca_taxonomica=0.0,
            distribuicao_resumida="",
            imagem_url="",
            imagem_fonte="",
            licenca_imagem="",
            ultima_validacao_em=None,
            enriquecimento_atualizado_em=None,
            save=MagicMock(),
        )

        result = pipeline.run_for_ponto(ponto, include_trefle=True, origem="teste")
        self.assertTrue(result["ok"])
        self.assertTrue(result["used_local_canonical"])
        self.assertEqual(ponto.integracoes_utilizadas, ["base_local"])
