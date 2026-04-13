# ColaboraPANC

> **Seletor de idioma:** [Português (Brasil)](./README.pt-BR.md) | [English](./README.md)

O ColaboraPANC é uma plataforma colaborativa open source para mapeamento georreferenciado de Plantas Alimentícias Não Convencionais (PANCs), integrando identificação assistida por IA, validação por especialistas, monitoramento ambiental e fluxos web/mobile. Seu propósito é ampliar a usabilidade científica, a rastreabilidade e a interpretação territorial de registros de biodiversidade contribuídos por cidadãos no contexto brasileiro.

## Público-alvo

- **Principal:** Pesquisadores, equipes de biodiversidade e segurança alimentar, gestores ambientais e iniciativas de ciência cidadã.
- **Secundário:** Educadores, projetos de extensão, ONGs e equipes técnicas que atuam com biodiversidade alimentar e monitoramento territorial.

## Funcionalidades principais

1. Registro colaborativo georreferenciado de observações de PANCs.
2. Suporte à identificação botânica assistida por IA.
3. Fluxo de validação por especialistas com histórico auditável.
4. Enriquecimento taxonômico com provedores externos.
5. Integrações de monitoramento ambiental e territorial.
6. Paridade mobile/web com fluxos apoiados por API.

**Fluxo principal:** Registro → inferência por IA → revisão especializada → registro validado → contexto territorial/ambiental.

## Stack técnica

- **Backend:** Django 4.2 + Django REST Framework + django-allauth
- **Frontend web:** Plataforma web servida pela stack Django / fluxos web apoiados por API
- **Aplicativo mobile:** Expo SDK 54 + React Native 0.81
- **Banco de dados:** PostgreSQL + PostGIS
- **APIs/serviços externos:** PlantNet, Plant.id, GBIF, iNaturalist, Tropicos, Global Names, Trefle, Wikipedia, MapBiomas, INMET, NASA FIRMS, Open-Meteo
- **Infraestrutura base:** VPS (4 GB RAM, 3 núcleos de CPU)
- **Dependências:** Python 3.11, PostgreSQL/PostGIS, GDAL, Node.js 18+
- **Sistemas operacionais suportados:** Linux, macOS, Windows (via Docker)

## Início rápido

### Backend

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements_core.txt
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

### Mobile

```bash
cd mobile
npm install
npm start
```

## Testes

```bash
# Testes locais básicos de backend
pytest

# Testes de backend CI/CD com cobertura
pytest tests/ mapping/tests.py --cov=mapping --cov-report=term-missing --cov-report=xml -v --tb=short

# Testes do app mobile
npm run test:ci

# Validação de lint/estilo do backend
flake8 mapping/ config/ tests/ --max-line-length=120 --exclude=mapping/migrations/,__pycache__ --count --statistics
```

## Documentação

- **Hub de documentação:** [`docs/README.md`](./docs/README.md)
- **Índice canônico em inglês:** [`docs/en/index.md`](./docs/en/index.md)
- **Índice canônico em português (Brasil):** [`docs/pt-BR/index.md`](./docs/pt-BR/index.md)
- **Guia de citação (EN):** [`docs/en/citation.md`](./docs/en/citation.md)
- **Guia de citação (PT-BR):** [`docs/pt-BR/citacao.md`](./docs/pt-BR/citacao.md)

## Citação, release e DOI

- **Nome do software:** ColaboraPANC
- **Versão:** 1.0.0
- **Release/tag:** https://github.com/warleynutricionista-jpg/colaborapanc/releases/tag/1.0.0
- **DOI arquival (Zenodo):** https://doi.org/10.5281/zenodo.19546445
- **Metadados preferenciais de citação:** [`CITATION.cff`](./CITATION.cff)

## Declaração breve de dados

O código-fonte do software é aberto. Um conjunto demonstrativo curado e materiais do repositório são disponibilizados para inspeção e reúso. Registros operacionais ou contribuídos por usuários com geolocalização sensível ou dados vinculados a contas não são divulgados publicamente.

## Metadados do projeto

- [Guia de Contribuição](./CONTRIBUTING.md)
- [Código de Conduta](./CODE_OF_CONDUCT.md)
- [Política de Segurança](./SECURITY.md)
- [Changelog](./CHANGELOG.md)
- [Licença](./LICENSE)
