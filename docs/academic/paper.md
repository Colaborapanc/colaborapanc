---
title: 'ColaboraPANC: An Open-Source Platform for AI-Assisted Geo-Referenced Mapping and Human-in-the-Loop Validation of Non-Conventional Food Plants'
tags:
  - Python
  - Django
  - citizen science
  - biodiversity
  - non-conventional food plants
  - geospatial
  - human-in-the-loop
  - food security
  - Brazil
authors:
  - name: Placeholder Author
    orcid: 0000-0000-0000-0000
    affiliation: 1
    # TODO: Replace with real name and ORCID before submission
affiliations:
  - name: Placeholder Institution, Brazil
    index: 1
    # TODO: Replace with real institution name before submission
date: 10 April 2026
bibliography: paper.bib
---

# Summary

ColaboraPANC is an open-source platform for collaborative, geo-referenced registration and scientific validation of Non-Conventional Food Plants (PANCs — *Plantas Alimentícias Não Convencionais*) in Brazil. PANCs are species with nutritional, culinary, or ecological value that are absent from mainstream food production chains but are present in urban and peri-urban environments, agroforestry systems, and traditional communities [@kinupp2014].

The platform integrates four technical components into a single auditable workflow: (1) geo-referenced field data collection via a React Native mobile application; (2) AI-assisted botanical identification through normalised calls to external providers (PlantNet [@plantnet] and Plant.id); (3) human-in-the-loop expert validation with full decision provenance; and (4) explainable territorial prioritisation based on a composite heuristic score. The backend is implemented in Django 4.2 with PostGIS spatial extensions [@postgis], exposing a Django REST Framework API consumed by the mobile client.

The scientific core of the system — models `PontoPANC`, `PredicaoIA`, `ValidacaoEspecialista`, and `HistoricoValidacao` — encodes a traceable cycle from raw citizen observation to expert-validated biodiversity record, with structured divergence tracking when AI predictions and human decisions differ.

# Statement of Need

Biodiversity monitoring of underutilised food plants faces a critical data-quality challenge: field observations collected by non-specialist contributors are heterogeneous in taxonomic precision, image quality, and geographic metadata. Existing general-purpose biodiversity platforms (e.g., iNaturalist [@inat], GBIF [@gbif]) provide observation infrastructure but do not implement role-restricted expert validation workflows, AI inference provenance tracking, or territorial prioritisation tailored to local socio-environmental conditions.

ColaboraPANC addresses this gap for the Brazilian PANC context by providing: a controlled validation pipeline that prevents unreviewed AI outputs from becoming final records; structured confidence classification with explicit risk bands (`faixa_risco`); auditability through a `HistoricoValidacao` event log; and a scientifically interpretable territorial score combining species incidence, climate risk, validation reliability, and observation recency. The result is a dataset-quality infrastructure that transforms distributed citizen observations into records suitable for food security planning, conservation prioritisation, and ecological research.

# Design and Implementation

## Architecture

The system follows a layered architecture separating concerns across three tiers:

- **Backend (Django 4.2 + PostGIS):** Domain logic is organised in `mapping/domains/` (analytics, AR, climate, gamification, offline, scientific, territorial, validation). Service integrations are in `mapping/services/` and include providers for botanical identification, taxonomic enrichment, environmental alerts, and climate data.
- **API (Django REST Framework):** RESTful endpoints documented in `docs/api_endpoints.md`. Scientific endpoints are prefixed `/api/cientifico/` and cover inference, validation queue, expert review, decision history, and the scientific dashboard.
- **Mobile (React Native / Expo):** Offline-capable client with screens for map visualisation, point registration, image capture, expert review panel, and push notifications.

## Scientific Workflow

The core workflow (`docs/fluxo_cientifico_do_sistema.md`) proceeds as follows:

1. **Registration:** A contributor records a `PontoPANC` with geolocation (`PointField`), photograph, and optional botanical context.
2. **AI Inference:** `POST /api/cientifico/pontos/<id>/inferencia/` calls configured external providers, normalises top-k predictions with confidence scores, classifies confidence into risk bands, and persists a `PredicaoIA` record.
3. **Review Queue:** `GET /api/cientifico/revisao/fila/` exposes pending validations to authorised reviewers, filterable by confidence band, status, and date window.
4. **Expert Validation:** `POST /api/cientifico/pontos/<id>/validacao/` records the specialist's decision in `ValidacaoEspecialista`, updating the point status (`validado`, `rejeitado`, or `necessita_revisao`) and logging a `HistoricoValidacao` event.
5. **Divergence Tracking:** When expert and AI conclusions differ, the field `motivo_divergencia` captures the specialist's reasoning, creating an explicit record of model limitations.
6. **Taxonomic Enrichment:** On save, an enrichment pipeline queries Global Names Verifier, Tropicos, GBIF, iNaturalist, Trefle, and Wikipedia to populate phenological and trait fields, with source attribution.
7. **Territorial Prioritisation:** `calcular_score_prioridade()` combines incidence weight, climate risk, validation reliability, and observation recency into an interpretable composite score used in the scientific dashboard.
8. **Scientific Dashboard:** `GET /api/cientifico/dashboard/` exposes aggregate metrics including validation rates, AI-expert agreement, confidence distribution, and temporal trends.

## Environmental Monitoring

The platform integrates real-time environmental signals via MapBiomas Alerta (deforestation alerts), NASA FIRMS (fire detection), INMET (meteorological alerts), and Open-Meteo (weather data). These are surfaced in the mobile client and the admin panel to provide ecological context for field observations.

# Example Data

The file `Pancs.csv` included in the repository provides a reference database of approximately 300 PANC species with common names, scientific names, plant type, edible parts, and primary use. This file serves as the seed for the offline plant identification module and as a reproducible example dataset for testing and demonstration.

# Testing

Automated tests cover the scientific core, AI identification providers, enrichment pipeline, environmental alerts, territorial prioritisation, and API permissions. The test suite is located in `tests/` (12 modules) and `mapping/tests.py`. Tests are executed with `pytest` and require a configured PostgreSQL/PostGIS database or a test-compatible SQLite fallback for unit-level tests. A GitHub Actions CI workflow (`.github/workflows/ci.yml`) runs the full suite on every push and pull request.

# Acknowledgements

The authors acknowledge the open-source communities behind Django, PostGIS, GeoDjango, React Native, Expo, PlantNet, GBIF, iNaturalist, and the scientific datasets that make the enrichment pipeline possible.

# References
