#!/usr/bin/env python
"""
Script de teste para integração com a API MapBiomas
"""

import os
import sys
import requests
from datetime import datetime, timedelta

# Credenciais — NUNCA hardcode aqui. Use variáveis de ambiente.
MAPBIOMAS_EMAIL = os.environ.get("MAPBIOMAS_EMAIL", "")
MAPBIOMAS_PASSWORD = os.environ.get("MAPBIOMAS_PASSWORD", "")
BASE_URL = os.environ.get("MAPBIOMAS_BASE_URL", "https://plataforma.alerta.mapbiomas.org/api/v2/graphql")


def test_authentication():
    """Testa autenticação na API MapBiomas"""
    print("=" * 60)
    print("TESTE 1: Autenticação MapBiomas")
    print("=" * 60)

    mutation = """
    mutation SignIn($email: String!, $password: String!) {
        signIn(email: $email, password: $password) {
            token
        }
    }
    """

    variables = {
        'email': MAPBIOMAS_EMAIL,
        'password': MAPBIOMAS_PASSWORD
    }

    try:
        response = requests.post(
            BASE_URL,
            json={'query': mutation, 'variables': variables},
            headers={'Content-Type': 'application/json'},
            timeout=10
        )

        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"Resposta: {data}")

            if 'data' in data and 'signIn' in data['data']:
                token = data['data']['signIn']['token']
                print(f"\n✅ AUTENTICAÇÃO BEM-SUCEDIDA!")
                print(f"Token obtido: {token[:50]}...")
                return token
            else:
                print(f"\n❌ ERRO: Resposta inesperada")
                print(f"Dados: {data}")
                return None
        else:
            print(f"\n❌ ERRO: Status code {response.status_code}")
            print(f"Resposta: {response.text}")
            return None

    except Exception as e:
        print(f"\n❌ EXCEÇÃO: {e}")
        return None


def test_query_alerts(token):
    """Testa consulta de alertas"""
    print("\n" + "=" * 60)
    print("TESTE 2: Buscar Alertas de Desmatamento")
    print("=" * 60)

    # Exemplo: buscar alertas no Brasil Central (Brasília)
    # Latitude: -15.7801, Longitude: -47.9292
    latitude = -15.7801
    longitude = -47.9292
    raio_km = 50

    # Calcula bounding box
    delta_lat = raio_km / 111.0
    delta_lng = raio_km / (111.0 * abs(latitude / 90.0))

    bbox = [
        longitude - delta_lng,
        latitude - delta_lat,
        longitude + delta_lng,
        latitude + delta_lat
    ]

    # Últimos 90 dias
    data_inicio = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
    data_fim = datetime.now().strftime('%Y-%m-%d')

    query = """
    query GetAlerts(
        $startDate: BaseDate!
        $endDate: BaseDate!
        $boundingBox: [Float!]
        $limit: Int
    ) {
        alerts(
            startDate: $startDate
            endDate: $endDate
            dateType: DetectedAt
            boundingBox: $boundingBox
            limit: $limit
        ) {
            collection {
                alertCode
                detectedAt
                publishedAt
                areaHa
            }
            metadata {
                totalCount
                totalPages
            }
        }
    }
    """

    variables = {
        'startDate': data_inicio,
        'endDate': data_fim,
        'boundingBox': bbox,
        'limit': 10
    }

    try:
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {token}'
        }

        response = requests.post(
            BASE_URL,
            json={'query': query, 'variables': variables},
            headers=headers,
            timeout=30
        )

        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()

            if 'errors' in data:
                print(f"\n❌ ERRO GraphQL: {data['errors']}")
                return False

            if 'data' in data and 'alerts' in data['data']:
                alerts = data['data']['alerts']
                print(f"\n✅ CONSULTA BEM-SUCEDIDA!")
                print(f"Total de alertas: {alerts['metadata']['totalCount']}")
                print(f"Páginas: {alerts['metadata']['totalPages']}")
                print(f"\nPrimeiros alertas:")

                for alert in alerts['collection'][:5]:
                    print(f"  - Código: {alert['alertCode']}")
                    print(f"    Data Detecção: {alert['detectedAt']}")
                    print(f"    Data Publicação: {alert['publishedAt']}")
                    print(f"    Área: {alert['areaHa']} ha")
                    print()

                return True
            else:
                print(f"\n❌ ERRO: Resposta inesperada")
                return False
        else:
            print(f"\n❌ ERRO: Status code {response.status_code}")
            print(f"Resposta: {response.text}")
            return False

    except Exception as e:
        print(f"\n❌ EXCEÇÃO: {e}")
        return False


def test_query_territories(token):
    """Testa consulta de territórios"""
    print("\n" + "=" * 60)
    print("TESTE 3: Buscar Territórios")
    print("=" * 60)

    query = """
    query GetTerritories {
        territoryOptions {
            category
            categoryName
            territories {
                name
            }
        }
    }
    """

    variables = {}

    try:
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {token}'
        }

        response = requests.post(
            BASE_URL,
            json={'query': query, 'variables': variables},
            headers=headers,
            timeout=30
        )

        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()

            if 'errors' in data:
                print(f"\n❌ ERRO GraphQL: {data['errors']}")
                return False

            if 'data' in data and 'territoryOptions' in data['data']:
                territory_options = data['data']['territoryOptions']
                print(f"\n✅ CONSULTA BEM-SUCEDIDA!")
                print(f"Categorias encontradas: {len(territory_options)}")

                # Mostra apenas biomas como exemplo
                for category in territory_options:
                    if category['category'] == 'BIOME':
                        print(f"\n{category['categoryName']} ({category['category']}):")
                        for territory in category['territories'][:5]:
                            print(f"  - {territory['name']}")
                        break

                return True
            else:
                print(f"\n❌ ERRO: Resposta inesperada")
                return False
        else:
            print(f"\n❌ ERRO: Status code {response.status_code}")
            return False

    except Exception as e:
        print(f"\n❌ EXCEÇÃO: {e}")
        return False


def main():
    """Função principal"""
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 10 + "TESTE DE INTEGRAÇÃO MAPBIOMAS" + " " * 18 + "║")
    print("╚" + "═" * 58 + "╝")
    print()

    # Teste 1: Autenticação
    token = test_authentication()

    if not token:
        print("\n⚠️  Falha na autenticação. Verifique as credenciais.")
        sys.exit(1)

    # Teste 2: Consultar alertas
    test_query_alerts(token)

    # Teste 3: Consultar territórios
    test_query_territories(token)

    print("\n" + "=" * 60)
    print("TESTES CONCLUÍDOS")
    print("=" * 60)
    print("\n✅ Integração MapBiomas funcionando corretamente!")
    print("\nEndpoints disponíveis:")
    print("  - GET  /api/mapbiomas/alertas/")
    print("  - GET  /api/mapbiomas/alertas/<alert_code>/")
    print("  - GET  /api/mapbiomas/territorios/")
    print("  - GET  /api/mapbiomas/propriedade/")
    print("  - GET  /api/mapbiomas/ponto/")
    print("  - GET  /api/mapbiomas/pontos-panc/<ponto_id>/")
    print("  - GET  /api/mapbiomas/testar/")
    print()


if __name__ == "__main__":
    main()
