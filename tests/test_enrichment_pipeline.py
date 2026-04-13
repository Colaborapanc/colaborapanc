from unittest.mock import Mock, patch

from django.contrib.gis.geos import Point
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIRequestFactory

from mapping.models import PontoPANC, PlantaReferencial
from mapping.serializers import PontoPANCSerializer
from mapping.services.enrichment.confidence import (
    calcular_grau_confianca_taxonomica,
    definir_status_enriquecimento,
)
from mapping.services.enrichment.normalizers import consolidar_resultados
from mapping.services.enrichment.planta_enrichment_pipeline import PlantaEnrichmentPipeline
from mapping.views import PontoPANCViewSet, api_health_integracoes


class EnrichmentUtilsTests(TestCase):
    def test_confidence_score_and_status(self):
        score = calcular_grau_confianca_taxonomica(
            gnv_ok=True,
            tropicos_ok=True,
            gbif_ok=True,
            inat_ok=False,
            conflito_taxonomico=False,
        )
        self.assertGreaterEqual(score, 0.8)
        self.assertEqual(definir_status_enriquecimento(4, 0, has_scientific_name=True), "completo")
        self.assertEqual(definir_status_enriquecimento(0, 3, has_scientific_name=True), "falho")

    def test_normalizer_priorities_and_required_fields(self):
        data = consolidar_resultados(
            scientific_name="Poa annua",
            gnv={"nome_cientifico_validado": "Poa annua", "nome_aceito": "Poa annua", "autoria": "L."},
            tropicos={"nome_aceito": "Poa annua L.", "autoria": "L.", "sinonimos": ["Poa reptans"]},
            gbif={"ocorrencias_gbif": 55, "distribuicao_resumida": "Plantae"},
            inat={"ocorrencias_inaturalist": 12, "fenologia_observada": "3, 4"},
            trefle={"comestivel": None, "edible_part": [], "fruit_months": []},
        )
        self.assertEqual(data["nome_aceito"], "Poa annua L.")
        self.assertEqual(data["comestibilidade_status"], "indeterminado")
        self.assertFalse(data["comestibilidade_confirmada"])
        self.assertIsNone(data["parte_comestivel"])
        self.assertIsNone(data["frutificacao_meses"])
        self.assertIsNone(data["colheita_periodo"])
        self.assertEqual(data["fontes_campos_enriquecimento"]["comestibilidade_status"], "nenhuma_fonte_confirmou")

    def test_normalizer_fallback_wikipedia_for_edible_fields(self):
        data = consolidar_resultados(
            scientific_name="Pereskia aculeata",
            gnv={"nome_cientifico_validado": "Pereskia aculeata"},
            tropicos={},
            gbif={},
            inat={},
            trefle={"comestivel": None, "edible_part": []},
            wikipedia={
                "fields": {
                    "comestivel": {"confirmed": True, "value": "sim"},
                    "parte_comestivel": {"confirmed": True, "value": "folhas, fruto"},
                }
            },
        )
        self.assertEqual(data["comestibilidade_status"], "sim")
        self.assertTrue(data["comestibilidade_confirmada"])
        self.assertEqual(data["parte_comestivel"], ["folha", "fruto"])
        self.assertTrue(data["parte_comestivel_confirmada"])


class EnrichmentPipelineTests(TestCase):
    def setUp(self):
        self.planta = PlantaReferencial.objects.create(nome_popular="Capim", nome_cientifico="Poa annua")
        self.ponto = PontoPANC.objects.create(
            planta=self.planta,
            nome_popular="Capim",
            localizacao=Point(-46.63, -23.55, srid=4326),
            latitude=-23.55,
            longitude=-46.63,
        )

    def test_pipeline_persists_partial_on_failures(self):
        pipeline = PlantaEnrichmentPipeline()
        pipeline.gnv.validate_name = Mock(return_value={"ok": True, "nome_cientifico_validado": "Poa annua", "nome_aceito": "Poa annua", "autoria": "L."})
        pipeline.tropicos.resolve = Mock(return_value={"ok": False, "error": "timeout"})
        pipeline.gbif.fetch = Mock(return_value={"ok": True, "ocorrencias_gbif": 10, "distribuicao_resumida": "Plantae"})
        pipeline.inat.fetch = Mock(return_value={"ok": False, "error": "timeout"})
        pipeline.trefle.fetch_optional_traits = Mock(return_value={"ok": True, "comestivel": True, "edible_part": ["leaf"], "fruit_months": [1, 2]})

        result = pipeline.run_for_ponto(self.ponto, include_trefle=True)
        self.ponto.refresh_from_db()

        self.assertTrue(result["ok"])
        self.assertEqual(self.ponto.status_enriquecimento, "parcial")
        self.assertIn("tropicos", self.ponto.payload_resumido_validacao["fontes_falharam"])
        self.assertEqual(self.ponto.comestibilidade_status, "sim")
        self.assertTrue(self.ponto.comestibilidade_confirmada)
        self.assertIn("integracoes_tentadas", self.ponto.payload_resumido_validacao)

    def test_pipeline_marks_review_when_taxonomic_ambiguity_detected(self):
        pipeline = PlantaEnrichmentPipeline()
        pipeline.gnv.validate_name = Mock(return_value={
            "ok": True,
            "nome_cientifico_validado": "Poa annua",
            "raw": {
                "data": [
                    {"bestResult": {"canonicalName": "Poa annua", "currentName": "Poa annua L."}},
                    {"bestResult": {"canonicalName": "Poa annua subsp. reptans", "currentName": "Poa annua subsp. reptans"}},
                ]
            },
        })
        pipeline.tropicos.resolve = Mock(return_value={"ok": True, "nome_aceito": "Poa annua L."})
        pipeline.gbif.fetch = Mock(return_value={"ok": True, "ocorrencias_gbif": 5})
        pipeline.inat.fetch = Mock(return_value={"ok": True, "ocorrencias_inaturalist": 4})
        pipeline.trefle.fetch_optional_traits = Mock(return_value={"ok": False, "error": "not_found"})

        result = pipeline.run_for_ponto(self.ponto, include_trefle=True)
        self.ponto.refresh_from_db()

        self.assertTrue(result["ok"])
        self.assertTrue(result["ambiguidade_taxonomica"]["ambiguous"])
        self.assertTrue(self.ponto.validacao_pendente_revisao_humana)
        self.assertIn("ambiguidade_taxonomica", self.ponto.payload_resumido_validacao)


class EnrichmentEndpointTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.planta = PlantaReferencial.objects.create(nome_popular="Capim", nome_cientifico="Poa annua")
        self.ponto = PontoPANC.objects.create(
            planta=self.planta,
            nome_popular="Capim",
            localizacao=Point(-46.63, -23.55, srid=4326),
            latitude=-23.55,
            longitude=-46.63,
        )

    @patch("mapping.views.plant_enrichment_pipeline")
    def test_revalidar_lote_endpoint(self, pipeline_mock):
        pipeline_mock.run_for_ponto.return_value = {"ok": True, "status_enriquecimento": "completo"}

        view = PontoPANCViewSet.as_view({"post": "revalidar_lote"})
        request = self.factory.post("/api/pontos/revalidar-lote/", {"ids": [self.ponto.id]}, format="json")
        response = view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["total"], 1)

    @patch("mapping.views.integration_health_service")
    def test_api_health_integracoes_superuser(self, health_mock):
        health_mock.check_all.return_value = [{"nome": "GBIF", "status": "online"}]
        user = get_user_model().objects.create_superuser("admin", "admin@example.com", "123")

        request = self.factory.get("/api/admin/integracoes/health/")
        request.user = user
        response = api_health_integracoes(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["integracoes"][0]["nome"], "GBIF")


class PontoCardSerializerTests(TestCase):
    def test_serializer_masks_tipo_outro_and_hides_empty_fields(self):
        planta = PlantaReferencial.objects.create(nome_popular="Ora-pro-nóbis", nome_cientifico="Pereskia aculeata")
        ponto = PontoPANC.objects.create(
            planta=planta,
            nome_popular="Ora-pro-nóbis",
            tipo_local="outro",
            localizacao=Point(-46.63, -23.55, srid=4326),
            latitude=-23.55,
            longitude=-46.63,
            comestibilidade_status="indeterminado",
            comestibilidade_confirmada=False,
            parte_comestivel_confirmada=False,
            frutificacao_confirmada=False,
            colheita_confirmada=False,
        )
        data = PontoPANCSerializer(ponto).data
        self.assertEqual(data["tipo_local_publico"], "local")
        self.assertIsNone(data["parte_comestivel"])
        self.assertIsNone(data["epoca_frutificacao"])
        self.assertIsNone(data["epoca_colheita"])
        self.assertIsNone(data["sazonalidade"])
