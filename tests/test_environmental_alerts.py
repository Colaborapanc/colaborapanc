from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from django.core.management import call_command
from django.test import TestCase, override_settings
from django.contrib.gis.geos import Point
from django.utils import timezone

from mapping.models import EventoMonitorado, PontoPANC, PlantaReferencial
from mapping.services.environmental_monitor_service import EnvironmentalMonitorService
from mapping.services.environmental_utils import build_bbox_from_point
from mapping.services.mapbiomas_alert_service import MapBiomasAlertService
from mapping.services.nasa_firms_service import NASAFirmsService


class EnvironmentalUtilsTests(TestCase):
    def test_build_bbox_from_point(self):
        bbox = build_bbox_from_point(-23.5, -46.6, 5000)
        self.assertEqual(len(bbox), 4)
        self.assertLess(bbox[0], -46.6)
        self.assertGreater(bbox[2], -46.6)


class ProviderParsingTests(TestCase):
    @override_settings(MAPBIOMAS_EMAIL="a@a.com", MAPBIOMAS_PASSWORD="x")
    @patch("mapping.services.mapbiomas_alert_service.requests.post")
    def test_mapbiomas_parsing(self, mock_post):
        auth_resp = Mock()
        auth_resp.raise_for_status = Mock()
        auth_resp.json.return_value = {"data": {"signIn": {"token": "abc"}}}

        data_resp = Mock()
        data_resp.raise_for_status = Mock()
        data_resp.json.return_value = {
            "data": {
                "alerts": {
                    "collection": [
                        {
                            "alertCode": 123,
                            "detectedAt": "2026-03-10T00:00:00Z",
                            "publishedAt": "2026-03-11T00:00:00Z",
                            "areaHa": 8.5,
                            "alertGeometry": {
                                "coordinates": [[[-46.6, -23.5], [-46.6, -23.4], [-46.5, -23.4], [-46.6, -23.5]]]
                            },
                            "statusName": "Confirmado",
                        }
                    ]
                }
            }
        }
        mock_post.side_effect = [auth_resp, data_resp]

        service = MapBiomasAlertService()
        items = service.fetch_alerts(-23.5, -46.6, 5000, days=7)

        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["fonte"], "mapbiomas")
        self.assertEqual(items[0]["tipo_evento"], "desmatamento")

    @override_settings(NASA_FIRMS_MAP_KEY="k", NASA_FIRMS_SOURCE="VIIRS_SNPP_NRT")
    @patch("mapping.services.nasa_firms_service.requests.Session.get")
    def test_firms_parsing(self, mock_get):
        response = Mock()
        response.raise_for_status = Mock()
        response.text = (
            "latitude,longitude,acq_date,acq_time,confidence,brightness,frp\n"
            "-23.51,-46.61,2026-03-11,1340,h,345.2,12.4\n"
        )
        mock_get.return_value = response

        service = NASAFirmsService()
        items = service.fetch_events(-23.5, -46.6, 5000, days=3)

        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["fonte"], "nasa_firms")
        self.assertIn(items[0]["tipo_evento"], ["foco_calor", "incendio"])


class DedupAndCommandTests(TestCase):
    def setUp(self):
        self.planta = PlantaReferencial.objects.create(nome_popular="Ora-pro-nóbis")
        self.ponto = PontoPANC.objects.create(
            planta=self.planta,
            localizacao=Point(-46.6, -23.5),
            latitude=-23.5,
            longitude=-46.6,
        )

    def test_deduplicacao_por_external_id(self):
        service = EnvironmentalMonitorService()
        result = type("Result", (), {"created": 0, "updated": 0, "errors": 0})()

        event = {
            "fonte": "mapbiomas",
            "tipo_evento": "desmatamento",
            "external_id": "abc-1",
            "hash_evento": "abc-1",
            "ocorrido_em": timezone.make_aware(datetime(2026, 3, 10, 10, 0, 0)),
            "descricao": "teste",
        }

        service._upsert_event(self.ponto, event, result)
        service._upsert_event(self.ponto, event, result)

        self.assertEqual(EventoMonitorado.objects.count(), 1)
        self.assertEqual(result.created, 1)
        self.assertEqual(result.updated, 1)

    @patch("mapping.management.commands.sincronizar_alertas_ambientais.EnvironmentalMonitorService.sync")
    def test_command_executes(self, mock_sync):
        mock_sync.return_value = type("Result", (), {"created": 2, "updated": 1, "errors": 0})()
        call_command("sincronizar_alertas_ambientais", "--ponto-id", str(self.ponto.id), "--fonte", "mapbiomas")
        mock_sync.assert_called_once()

    @patch("mapping.management.commands.sincronizar_alertas_ambientais.EnvironmentalMonitorService.sync")
    def test_command_latest_only(self, mock_sync):
        mock_sync.return_value = type("Result", (), {"created": 1, "updated": 0, "errors": 0})()
        call_command(
            "sincronizar_alertas_ambientais",
            "--ponto-id",
            str(self.ponto.id),
            "--latest-only",
        )
        mock_sync.assert_called_once()
        self.assertTrue(mock_sync.call_args.kwargs["latest_only"])

    def test_filtra_eventos_mais_antigos_que_um_ano(self):
        service = EnvironmentalMonitorService()
        agora = timezone.now()
        antigos = [
            {"ocorrido_em": agora - timedelta(days=400)},
            {"ocorrido_em": agora - timedelta(days=10)},
        ]
        filtrados = service._filtrar_janela_ultimo_ano(antigos)
        self.assertEqual(len(filtrados), 1)

    def test_latest_only_mantem_evento_mais_recente(self):
        service = EnvironmentalMonitorService()
        result = type("Result", (), {"created": 0, "updated": 0, "errors": 0})()
        eventos = [
            {
                "fonte": "mapbiomas",
                "tipo_evento": "desmatamento",
                "external_id": "old",
                "hash_evento": "old",
                "ocorrido_em": timezone.make_aware(datetime(2026, 1, 1, 10, 0, 0)),
            },
            {
                "fonte": "mapbiomas",
                "tipo_evento": "desmatamento",
                "external_id": "new",
                "hash_evento": "new",
                "ocorrido_em": timezone.make_aware(datetime(2026, 1, 2, 10, 0, 0)),
            },
        ]
        service._sync_provider(
            provider_name="mapbiomas",
            fetcher=lambda: eventos,
            ponto=self.ponto,
            result=result,
            latest_only=True,
        )
        self.assertEqual(EventoMonitorado.objects.count(), 1)
        self.assertEqual(EventoMonitorado.objects.first().external_id, "new")
