# ColaboraPANC

> **Seletor de idioma:** [Português (Brasil)](./README.pt-BR.md) | [English](./README.md)

O ColaboraPANC é uma plataforma colaborativa open source para mapeamento georreferenciado de Plantas Alimentícias Não Convencionais (PANC), unindo contribuição comunitária, fluxos científicos assistidos por IA, monitoramento ambiental e paridade entre web e mobile.

## O que o sistema inclui atualmente

### 1) Plataforma backend (Django + DRF)
- Fluxos web para visualização em mapa, contribuição, curadoria, moderação e painéis administrativos.
- Endpoints REST para pontos, recursos de colaboração, rotas, notificações e preferências de usuário.
- Fluxos de autenticação e contas via login por token, registro e rotas de conta do django-allauth.

### 2) Fluxo científico e validação assistida por IA
- Endpoint de inferência por IA para suporte à identificação botânica no fluxo científico.
- Fila de revisão, detalhe por ponto em revisão, decisão de validação e histórico auditável de decisões.
- Lógica de classificação por confiança/risco e serviços de priorização em nível de domínio.

### 3) Integrações ambientais e territoriais
- Endpoints de alertas MapBiomas (alertas, detalhamento, territórios, consultas por CAR/propriedade e análise por ponto).
- Endpoints de alertas climáticos (alertas ativos, histórico, status operacional e sincronização).
- Priorização territorial e serviços de domínio para contexto ambiental.

### 4) Aplicativo mobile (Expo/React Native)
- Cliente mobile dedicado com Expo SDK 54 e React Native 0.81.
- Endpoints de paridade mobile para identificação por imagem, previews de mapa e metadados/download de base offline.
- Scripts para Android, iOS, web, diagnóstico e testes mobile orientados a CI.

### 5) Módulos auxiliares de colaboração
- Fluxos de notificações e token de push.
- APIs de conversas/mensagens.
- Gamificação, missões, rankings e experiências de comunidades/grupos.
- Capacidades de enriquecimento e saúde de integrações com provedores externos.

### 6) Testes e operação
- Suíte automatizada em `tests/` cobrindo núcleo científico, permissões, enriquecimento, integrações, clima, alertas ambientais e serviços relacionados.
- Rotas operacionais como healthcheck (`/healthz/`) e endpoints administrativos de status/teste de integrações.

## Stack tecnológica atual

- **Backend:** Django 4.2, Django REST Framework, django-allauth.
- **Banco de dados:** PostgreSQL + PostGIS.
- **Dependências GIS:** GDAL.
- **Mobile:** Expo SDK 54, React Native 0.81.
- **Testes:** pytest + pytest-django (backend), jest/jest-expo (mobile).

## Início rápido

### Backend

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements_core.txt
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

URL local padrão: `http://localhost:8000`.

### Mobile

```bash
cd mobile
npm install
npm start
```

## Portas de entrada da documentação

- **Hub de documentação:** [`docs/README.md`](./docs/README.md)
- **Índice canônico em inglês:** [`docs/en/index.md`](./docs/en/index.md)
- **Índice canônico em português (Brasil):** [`docs/pt-BR/index.md`](./docs/pt-BR/index.md)

## Metadados do projeto

- [Guia de Contribuição](./CONTRIBUTING.md)
- [Código de Conduta](./CODE_OF_CONDUCT.md)
- [Política de Segurança](./SECURITY.md)
- [Changelog](./CHANGELOG.md)
- [Licença](./LICENSE)
