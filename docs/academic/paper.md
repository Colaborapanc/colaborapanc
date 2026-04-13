---
title: 'ColaboraPANC: An Open-Source Citizen Science Platform for AI-Assisted Georeferenced Mapping and Expert Validation of Non-Conventional Food Plants in Brazil'
subtitle: 'Internal editorial draft for SoftwareX preparation (not the official journal template)'
tags:
  - Python
  - JavaScript
  - Django
  - citizen science
  - biodiversity informatics
  - food security
  - environmental monitoring
  - geospatial systems
authors:
  - name: Warley Alisson Souza
    orcid: 0000-0003-2063-1531
    affiliation: 1
    email: warleyalisson@gmail.com
  - name: Raquel Linhares Bello de Araujo
    orcid: 0000-0002-5110-5203
    affiliation: 1
    email: raquellba.linhares@gmail.com
  - name: Marinalva Woods Pedrosa
    orcid: 0000-0002-4850-7615
    affiliation: 2
    email: marinalva@epamig.br
  - name: Julio Onesio-Ferreira Melo
    orcid: 0000-0002-7483-0942
    affiliation: 3
    email: onesiomelo@gmail.com
affiliations:
  - name: Universidade Federal de Minas Gerais (UFMG), Belo Horizonte, Minas Gerais, Brazil
    index: 1
  - name: Empresa de Pesquisa Agropecuária de Minas Gerais (EPAMIG), Minas Gerais, Brazil
    index: 2
  - name: Universidade Federal de São João del-Rei (UFSJ), Sete Lagoas, Minas Gerais, Brazil
    index: 3
date: 12 April 2026
bibliography: paper.bib
---

# Editorial status

This file is an internal editorial draft for SoftwareX preparation. It consolidates agreed metadata and manuscript content, but it is not the official journal submission template.

## Submission type

Original software publication.

## Corresponding author

Warley Alisson Souza (warleyalisson@gmail.com).

# Software description

ColaboraPANC is an open-source collaborative platform for georeferenced mapping of non-conventional food plants (PANCs), integrating AI-assisted identification, expert validation, environmental monitoring, and web/mobile workflows. Its purpose is to improve the scientific usability, traceability, and territorial interpretation of citizen-contributed biodiversity records related to underutilized edible plants in Brazil.

# Problem statement

Transforming collaborative observations of non-conventional food plants into auditable, georeferenced, and scientifically usable records by combining citizen contribution, AI-assisted support, expert validation, and territorial/environmental context.

# Scope, areas, and audience

- **Main areas:** Citizen science; biodiversity informatics; food security; environmental monitoring; geospatial systems.
- **Primary audience:** Researchers, biodiversity and food security teams, environmental managers, and citizen science initiatives.
- **Secondary audience:** Educators, extension projects, NGOs, and technical teams working with edible biodiversity and territorial monitoring.

# Distinguishing features

- Role-restricted expert validation.
- Human-in-the-loop decision provenance.
- AI prediction persistence and divergence tracking.
- Territorial prioritization.
- Integration of environmental alerts.
- Focus on PANCs rather than generic biodiversity records.

# Core functionality and workflow

1. Georeferenced collaborative registration of PANC observations.
2. AI-assisted plant identification support.
3. Expert validation workflow with auditable history.
4. Taxonomic enrichment from external providers.
5. Environmental and territorial monitoring integrations.
6. Mobile/web parity with API-backed workflows.

**Main workflow:** Registration → AI inference → expert review → validated record → territorial/environmental context.

# Technical stack

- **Backend:** Django 4.2 + Django REST Framework + django-allauth.
- **Web frontend:** Web platform served by the Django stack / API-backed web flows.
- **Mobile app:** Expo SDK 54 + React Native 0.81.
- **Database:** PostgreSQL + PostGIS.
- **External APIs/services:** PlantNet, Plant.id, GBIF, iNaturalist, Tropicos, Global Names, Trefle, Wikipedia, MapBiomas, INMET, NASA FIRMS, Open-Meteo.
- **Infrastructure baseline:** VPS (4 GB RAM, 3 CPU cores).
- **Dependencies:** Python 3.11, PostgreSQL/PostGIS, GDAL, Node.js 18+.
- **Supported OS:** Linux, macOS, Windows (via Docker).

# Quantitative validation highlights

- Validation and rejection rates.
- AI vs expert agreement and divergence (top-1).
- Inference confidence distribution (high, medium, low).
- Average time to validation (in hours).

**Recommended strongest metric:** AI vs expert agreement/divergence (top-1), because it directly quantifies the behavior of the AI-assisted workflow against the final human expert decision.

# Data statement

The software source code is openly available. A curated demonstration dataset and repository materials will be made publicly available to support inspection and reuse of the software. Operational or user-contributed records containing sensitive geolocation or account-linked information are not released publicly; only non-sensitive, reproducible example data are provided.

# Funding

This work was supported by CNPq, FAPEMIG, and CAPES. Grant or process numbers were not available at the time of submission.

# Acknowledgements

The authors acknowledge the support of CNPq, FAPEMIG, CAPES, UFMG, UFSJ, EPAMIG, and GEPEQF.

# Conflict of interest

The authors declare that they have no known competing interests.

# Generative AI declaration

Generative AI was used for grammatical improvements and translation support during manuscript preparation. All generated outputs were reviewed, edited, and validated by the authors, who take full responsibility for the final content of the manuscript.

# Author contributions (CRediT)

- **Warley Alisson Souza:** Conceptualization; Software; Methodology; Data curation; Visualization; Writing – original draft.
- **Raquel Linhares Bello de Araujo:** Supervision; Conceptualization; Methodology; Writing – review & editing.
- **Marinalva Woods Pedrosa:** Resources; Validation; Writing – review & editing.
- **Julio Onesio-Ferreira Melo:** Methodology; Validation; Writing – review & editing.

# SoftwareX metadata table (C1–C9)

- **C1 — Current code version:** 1.0.1
- **C2 — Permanent link to code/repository used for this code version:** https://doi.org/10.5281/zenodo.19546738
- **C3 — Permanent link to Reproducible Capsule:** N/A
- **C4 — Legal Code License:** MIT
- **C5 — Code versioning system used:** Git
- **C6 — Software code languages, tools, and services used:** Python; JavaScript; Django 4.2; Django REST Framework; PostgreSQL/PostGIS; React Native; Expo; external enrichment and environmental services
- **C7 — Compilation requirements, operating environments & dependencies:** Python >= 3.11; PostgreSQL >= 12 with PostGIS; GDAL >= 3.0; Node.js >= 18; Linux/macOS/Windows via Docker
- **C8 — Link to developer documentation/manual:** https://github.com/warleynutricionista-jpg/colaborapanc/blob/main/docs/en/index.md
- **C9 — Support email for questions:** warleyalisson@gmail.com

# Availability and archiving

- **GitHub release used for this version:** https://github.com/warleynutricionista-jpg/colaborapanc/releases/tag/1.0.1
- **Archival DOI:** https://doi.org/10.5281/zenodo.19546738
- **Archival platform:** Zenodo

# Recommended figures for manuscript assembly

1. Overall software architecture.
2. Scientific workflow from citizen record submission to expert-validated output.
3. External integrations and enrichment pipeline.
4. Representative web/mobile interface or dashboard.
5. Auditable AI suggestion versus expert validation trail.
