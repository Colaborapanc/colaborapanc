# Módulos

## Módulos do backend (`mapping/`)

- **Núcleo de mapeamento e contribuição** (`views.py`, `models.py`, `forms.py`).
- **API REST e fluxo científico** (`views_api.py`, serializers).
- **AR e identificação avançada** (`views_ar_identificacao.py`).
- **Plantas offline seletivas** (`views_offline_plantas.py`).
- **Módulo MapBiomas** (`views_mapbiomas.py`, serviços mapbiomas).
- **Módulo de clima** (`views_climate.py`, serviços de alerta).
- **Módulo de enriquecimento** (`views_enrichment.py`, serviços de enrichment).
- **Módulo de paridade mobile** (`views_mobile_parity.py`, `mobile_parity_service.py`).

## Módulos do mobile (`mobile/src/`)

- Telas de mapa e cadastro.
- Telas de revisão e notificações.
- Configuração de API e utilitários para enriquecimento/estado offline.

## Testes (`tests/`)

Cobertura inclui núcleo científico, permissões, saúde de integrações, pipeline de enriquecimento, mapbiomas, identificação botânica, alertas climáticos e serviços relevantes ao mobile.
