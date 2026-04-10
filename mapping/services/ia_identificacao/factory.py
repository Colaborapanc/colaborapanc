import os
from .plantnet_provider import PlantNetProvider
from .plantid_provider import PlantIdProvider


def build_providers(plantid_api_key: str = ''):
    api_key = plantid_api_key or os.environ.get('PLANTID_API_KEY', '')
    return [PlantNetProvider(), PlantIdProvider(api_key=api_key)]
