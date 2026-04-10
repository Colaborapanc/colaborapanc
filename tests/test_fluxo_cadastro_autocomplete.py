from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.gis.geos import Point
from django.test import TestCase

from mapping.models import PontoPANC, PlantaReferencial


class AutocompleteNomePopularTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="tester", password="123456")
        self.client.force_login(self.user)
        PlantaReferencial.objects.create(
            nome_popular="Ora-pro-nóbis",
            nome_cientifico="Pereskia aculeata",
        )
        PlantaReferencial.objects.create(
            nome_popular="Taioba",
            nome_cientifico="Xanthosoma taioba",
        )

    def test_autocomplete_detalhado_retorna_nome_cientifico_e_origem(self):
        response = self.client.get("/api/autocomplete-nome/", {"term": "ora", "detailed": "1"})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(any(item["nome_popular"] == "Ora-pro-nóbis" for item in data))
        item = next(i for i in data if i["nome_popular"] == "Ora-pro-nóbis")
        self.assertEqual(item["nome_cientifico"], "Pereskia aculeata")
        self.assertEqual(item["source"], "base_local_validada")

    @patch("mapping.views.requests.get")
    def test_autocomplete_fallback_local_quando_integracao_externa_falha(self, requests_get):
        requests_get.side_effect = Exception("timeout")
        response = self.client.get("/api/autocomplete-nome/", {"term": "tai", "detailed": "1"})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(any(item["nome_popular"] == "Taioba" for item in data))

    def test_busca_nome_cientifico_retorna_origem(self):
        response = self.client.get("/api/nome-cientifico/", {"nome_popular": "Ora-pro-nóbis"})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["nome_cientifico"], "Pereskia aculeata")
        self.assertEqual(data["source"], "base_local_validada")
        self.assertTrue(data["resolved"])


class DetalhePontoStatusUXTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="user", password="123456")
        self.superuser = get_user_model().objects.create_superuser(
            username="admin",
            password="123456",
            email="admin@example.com",
        )
        self.planta = PlantaReferencial.objects.create(
            nome_popular="Taioba",
            nome_cientifico="Xanthosoma taioba",
        )
        self.ponto = PontoPANC.objects.create(
            planta=self.planta,
            nome_popular="Taioba",
            localizacao=Point(-46.63, -23.55, srid=4326),
            latitude=-23.55,
            longitude=-46.63,
            status_enriquecimento="pendente",
            colaborador="user",
        )

    def test_usuario_comum_nao_ve_status_pendente_enriquecimento(self):
        self.client.force_login(self.user)
        response = self.client.get(f"/ponto/{self.ponto.id}/")
        self.assertEqual(response.status_code, 200)
        content = response.content.decode("utf-8")
        self.assertNotIn("Status interno do enriquecimento", content)
        self.assertNotIn('<span class="badge bg-secondary">Pendente</span>', content)

    def test_admin_ve_status_interno_enriquecimento(self):
        self.client.force_login(self.superuser)
        response = self.client.get(f"/ponto/{self.ponto.id}/")
        self.assertEqual(response.status_code, 200)
        content = response.content.decode("utf-8")
        self.assertIn("Status interno do enriquecimento", content)

    def test_cadastro_exibe_campos_alimentares_manuais(self):
        self.client.force_login(self.user)
        response = self.client.get("/cadastro/")
        self.assertEqual(response.status_code, 200)
        content = response.content.decode("utf-8")
        self.assertIn("id_comestibilidade_status", content)
        self.assertIn("id_parte_comestivel_manual", content)
        self.assertIn("id_frutificacao_manual", content)
        self.assertIn("id_colheita_manual", content)

    def test_api_create_persiste_campos_manuais_sem_sobrescrever_confirmados(self):
        self.client.force_login(self.user)
        payload = {
            "nome_popular": "Taioba nova",
            "nome_cientifico": "Xanthosoma taioba",
            "tipo_local": "quintal",
            "localizacao": [-46.63, -23.55],
            "comestibilidade_status": "sim",
            "parte_comestivel_manual": "folha, caule",
            "frutificacao_manual": "jan, fev",
            "colheita_manual": "mar, abr",
            "enriquecer_automaticamente": False,
        }
        response = self.client.post("/api/pontos/", data=payload, content_type="application/json")
        self.assertEqual(response.status_code, 201)
        ponto = PontoPANC.objects.get(id=response.json()["id"])
        self.assertEqual(ponto.comestibilidade_status, "sim")
        self.assertTrue(ponto.comestibilidade_confirmada)
        self.assertEqual(ponto.parte_comestivel_lista, ["folha", "caule"])
        self.assertEqual(ponto.frutificacao_meses, ["jan", "fev"])
        self.assertEqual(ponto.colheita_periodo, ["mar", "abr"])
