from datetime import timedelta
from unittest.mock import Mock, patch

import requests
from django.contrib.gis.geos import Point
from django.test import TestCase, override_settings
from django.utils import timezone

from mapping.models import AlertaClimatico, PontoPANC, PlantaReferencial
from mapping.services.climate_alert_service import ClimateAlertService


class ClimateAlertServiceTests(TestCase):
    def setUp(self):
        planta = PlantaReferencial.objects.create(nome_popular="Taioba")
        self.ponto = PontoPANC.objects.create(
            planta=planta,
            nome_popular="Taioba",
            cidade="Campinas",
            estado="SP",
            localizacao=Point(-47.06, -22.90),
            latitude=-22.90,
            longitude=-47.06,
        )

    @override_settings(INMET_ALERTS_FEED_URL="https://example.com/rss", OPENMETEO_API_URL="https://example.com/open-meteo")
    @patch("mapping.services.mapbiomas_alert_service.requests.post")
    @patch("mapping.services.climate_alert_service.requests.get")
    def test_sync_cria_alertas_e_deduplica(self, mock_get, mock_mapbiomas_post):
        rss_response = Mock()
        rss_response.raise_for_status = Mock()
        rss_response.text = """
        <rss><channel>
            <item><title>Perigo de chuva forte em SP</title><description>Campinas e região</description><pubDate>Mon, 07 Apr 2026 12:00:00 GMT</pubDate></item>
            <item><title>Perigo de chuva forte em SP</title><description>Campinas e região</description><pubDate>Mon, 07 Apr 2026 12:00:00 GMT</pubDate></item>
        </channel></rss>
        """

        meteo_response = Mock()
        meteo_response.raise_for_status = Mock()
        meteo_response.json.return_value = {
            "hourly": {
                "time": ["2026-04-07T10:00:00-03:00"],
                "precipitation": [25],
                "temperature_2m": [37],
                "windspeed_10m": [65],
            }
        }
        mock_get.side_effect = [rss_response, meteo_response]

        auth_resp = Mock()
        auth_resp.raise_for_status = Mock()
        auth_resp.json.return_value = {"data": {"signIn": {"token": "abc"}}}

        data_resp = Mock()
        data_resp.raise_for_status = Mock()
        data_resp.json.return_value = {"data": {"alerts": {"collection": []}}}
        mock_mapbiomas_post.side_effect = [auth_resp, data_resp]

        service = ClimateAlertService()
        result = service.sync(ponto_id=self.ponto.id)

        self.assertGreaterEqual(result.created, 3)
        self.assertEqual(result.errors, 0)
        self.assertEqual(AlertaClimatico.objects.count(), result.created)

    @patch("mapping.services.climate_alert_service.requests.get")
    def test_sync_tolerates_partial_provider_failure(self, mock_get):
        mock_get.side_effect = requests.exceptions.Timeout("timeout")
        service = ClimateAlertService()

        with patch.object(service, "_fetch_mapbiomas_alerts", return_value=[]):
            result = service.sync(ponto_id=self.ponto.id)

        self.assertEqual(result.errors, 0)
        self.assertTrue(any(not item.ok for item in result.provider_status))

    def test_get_active_alerts_filtra_expirados(self):
        now = timezone.now()
        AlertaClimatico.objects.create(
            ponto=self.ponto,
            tipo="Chuva forte",
            severidade="alta",
            descricao="ativo",
            inicio=now - timedelta(hours=1),
            fim=now + timedelta(hours=1),
            fonte="INMET",
        )
        AlertaClimatico.objects.create(
            ponto=self.ponto,
            tipo="Vento forte",
            severidade="media",
            descricao="expirado",
            inicio=now - timedelta(days=2),
            fim=now - timedelta(days=1),
            fonte="INMET",
        )

        service = ClimateAlertService()
        ativos = service.get_active_alerts(ponto_id=self.ponto.id)
        self.assertEqual(len(ativos), 1)
        self.assertEqual(ativos[0].descricao, "ativo")
