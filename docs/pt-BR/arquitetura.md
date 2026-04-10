# Arquitetura

## Componentes de alto nível

1. **Backend web/API**: projeto Django (`config/`, `mapping/`).
2. **Camada de dados geoespaciais**: PostgreSQL + PostGIS.
3. **Aplicativo mobile**: Expo + React Native (`mobile/`).
4. **Camada de integrações**: identificação botânica, enriquecimento, clima e serviços ambientais.

## Fluxos funcionais principais

- Ciclo de ponto: cadastro → inferência IA → revisão → validação.
- Análise ambiental: snapshots climáticos + alertas MapBiomas.
- Paridade mobile: lógica compartilhada web/mobile para identificação e metadados offline.

## Referências técnicas principais

- Composição de URLs: `config/urls.py`, `mapping/urls.py`.
- Modelo de domínio: `mapping/models.py`.
- Serviços centrais: `mapping/services/`.
- Views API/web: `mapping/views.py`, `mapping/views_api.py` e arquivos especializados `views_*`.
