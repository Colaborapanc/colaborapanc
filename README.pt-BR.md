# ColaboraPANC

> **Idioma / Language:** [Português (Brasil)](./README.pt-BR.md) | [English](./README.md)

O ColaboraPANC é uma plataforma colaborativa open source para mapeamento georreferenciado de Plantas Alimentícias Não Convencionais (PANC), com identificação assistida por IA, fluxo de revisão humana e análise ambiental/territorial.

## Visão Geral do Projeto

O ColaboraPANC integra:
- Backend Django + Django REST Framework para fluxos web e APIs.
- Camada geoespacial PostgreSQL/PostGIS.
- Aplicativo mobile em Expo/React Native.
- Serviços de integração para identificação botânica, enriquecimento taxonômico, alertas climáticos e alertas ambientais do MapBiomas.

## Funcionalidades Centrais Atuais

- Cadastro e curadoria de pontos PANC georreferenciados.
- Fluxo científico: inferência por IA, fila de revisão, validação e histórico de decisões.
- Endpoints de paridade mobile para identificação por imagem e metadados/download de base offline.
- Módulos ambientais e territoriais (MapBiomas, alertas climáticos e priorização territorial).
- Módulos auxiliares de notificações, conversas/mensagens, rotas e preferências de usuário.

## Stack Tecnológica

- **Backend:** Django 4.2, Django REST Framework, django-allauth.
- **Banco de dados:** PostgreSQL + PostGIS.
- **Dependências GIS:** GDAL.
- **Mobile:** Expo SDK 54 + React Native.
- **Testes:** pytest + pytest-django.

## Início Rápido

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

## Documentação

- **Índice da documentação em português:** [`docs/pt-BR/index.md`](./docs/pt-BR/index.md)
- **Índice da documentação em inglês:** [`docs/en/index.md`](./docs/en/index.md)
- **Hub de documentação:** [`docs/README.md`](./docs/README.md)

## Metadados do Projeto

- [Guia de Contribuição](./CONTRIBUTING.md)
- [Código de Conduta](./CODE_OF_CONDUCT.md)
- [Política de Segurança](./SECURITY.md)
- [Changelog](./CHANGELOG.md)
- [Licença](./LICENSE)
