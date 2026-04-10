import os
import tempfile
import pytest
from django.test import TestCase
from utils.plant_identification import (
    identificar_especie,
    can_use_api,
    increment_api_usage,
    get_or_create_api_log,
    PLANTID_MONTHLY_LIMIT,
    PLANTNET_MONTHLY_LIMIT,
)

from mapping.models import APIUsageLog


@pytest.mark.django_db
class TestPlantIdentification(TestCase):
    def setUp(self):
        # Zera logs
        APIUsageLog.objects.all().delete()
        # Cria imagem fake temporária
        self.temp_img = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
        self.temp_img.write(b"\x00\x01\x02\x03\x04\x05")  # bytes mínimos
        self.temp_img.flush()

    def tearDown(self):
        try:
            os.unlink(self.temp_img.name)
        except Exception:
            pass

    def test_controla_limite_plantid(self):
        """Testa controle de uso para Plant.id."""
        for _ in range(PLANTID_MONTHLY_LIMIT):
            assert can_use_api("Plant.id", PLANTID_MONTHLY_LIMIT)
            increment_api_usage("Plant.id", PLANTID_MONTHLY_LIMIT)
        assert not can_use_api("Plant.id", PLANTID_MONTHLY_LIMIT)  # Limite atingido

    def test_controla_limite_plantnet(self):
        """Testa controle de uso para PlantNet."""
        for _ in range(PLANTNET_MONTHLY_LIMIT):
            assert can_use_api("PlantNet", PLANTNET_MONTHLY_LIMIT)
            increment_api_usage("PlantNet", PLANTNET_MONTHLY_LIMIT)
        assert not can_use_api("PlantNet", PLANTNET_MONTHLY_LIMIT)

    def test_fallback_manual_quando_limite(self, monkeypatch):
        """Testa fallback para manual quando ambos limites atingidos."""
        # Simula limites atingidos
        log1 = get_or_create_api_log("Plant.id", PLANTID_MONTHLY_LIMIT)
        log1.used = PLANTID_MONTHLY_LIMIT
        log1.save()
        log2 = get_or_create_api_log("PlantNet", PLANTNET_MONTHLY_LIMIT)
        log2.used = PLANTNET_MONTHLY_LIMIT
        log2.save()
        resultado = identificar_especie(self.temp_img.name)
        assert resultado["fallback"] is True
        assert "Utilize o cadastro manual" in resultado["mensagem"]

    def test_fallback_plantnet_quando_plantid_falha(self, monkeypatch):
        """Testa fallback para PlantNet se Plant.id falhar."""
        # Simula Plant.id falhando (mock)
        def fake_plantid(img):
            return {"success": False, "error": "API error"}

        def fake_plantnet(img):
            return {
                "success": True,
                "nome_cientifico": "Ficticia testii",
                "nomes_populares": ["Fictícia"],
                "raw": {},
            }

        monkeypatch.setattr("utils.plant_identification.call_plant_id_api", fake_plantid)
        monkeypatch.setattr("utils.plant_identification.call_plantnet_api", fake_plantnet)
        resultado = identificar_especie(self.temp_img.name)
        assert resultado["nome_cientifico"] == "Ficticia testii"
        assert resultado["api_usada"] == "PlantNet"

    def test_identificacao_ok_plantid(self, monkeypatch):
        """Testa identificação bem-sucedida via Plant.id."""
        def fake_plantid(img):
            return {
                "success": True,
                "nome_cientifico": "Testus plantis",
                "nomes_populares": ["Testuda"],
                "raw": {},
            }

        monkeypatch.setattr("utils.plant_identification.call_plant_id_api", fake_plantid)
        resultado = identificar_especie(self.temp_img.name)
        assert resultado["nome_cientifico"] == "Testus plantis"
        assert resultado["api_usada"] == "Plant.id"


@pytest.mark.integration
def test_identificacao_api():
    if os.environ.get("RUN_INTEGRATION_TESTS") != "1":
        pytest.skip("Defina RUN_INTEGRATION_TESTS=1 para rodar o teste de integração.")
    image_path = os.environ.get("PLANT_IMAGE_PATH")
    if not image_path or not os.path.exists(image_path):
        pytest.skip("Defina PLANT_IMAGE_PATH com uma imagem válida para o teste.")
    url = "http://localhost:8000/api/identificar/"
    import requests

    with open(image_path, "rb") as img:
        files = {"foto": img}
        resp = requests.post(url, files=files, timeout=30)
        assert resp.status_code == 200
