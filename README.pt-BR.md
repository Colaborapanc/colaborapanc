# ColaboraPANC

> Seletor de idioma: [Português (Brasil)](./README.pt-BR.md) | [English](./README.md)

> **Referência para submissão internacional:** a versão canônica para avaliação técnico-editorial internacional é o [`README.md` em inglês](./README.md).

O ColaboraPANC é uma plataforma open source para mapeamento georreferenciado e validação científica de PANCs (Plantas Alimentícias Não Convencionais), unindo coleta colaborativa, suporte de IA, revisão humana especializada e integrações ambientais.

## Visão geral

O repositório reúne:

- backend em Django + DRF;
- aplicativo mobile em React Native/Expo;
- módulos de validação científica, enriquecimento taxonômico, alertas ambientais e priorização territorial;
- documentação canônica bilíngue.

## Navegação principal

- Documento principal internacional (EN): [`README.md`](./README.md)
- Hub de documentação: [`docs/README.md`](./docs/README.md)
- Índice canônico em inglês: [`docs/en/index.md`](./docs/en/index.md)
- Índice canônico em PT-BR: [`docs/pt-BR/index.md`](./docs/pt-BR/index.md)

## Instalação rápida (resumo)

### Backend

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements_core.txt
cp .env.example .env
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

### Mobile

```bash
cd mobile
npm install
npm start
```

## Documentos de apoio para submissão SoftwareX

- Auditoria editorial inicial: [`docs/en/editorial_audit.md`](./docs/en/editorial_audit.md)
- Estrutura do projeto: [`docs/en/project_structure.md`](./docs/en/project_structure.md)
- Reprodutibilidade: [`docs/en/reproducibility.md`](./docs/en/reproducibility.md)
- Testes e validação: [`docs/en/testing.md`](./docs/en/testing.md)
- Citação provisória: [`docs/en/citation.md`](./docs/en/citation.md)

## Observações importantes

- DOI/PID, release pública formal e submissão editorial dependem de ações externas dos mantenedores/autores.
- Metadados de autoria/afiliação devem ser confirmados manualmente antes da submissão final.

## Metadados e governança

- [Guia de Contribuição](./CONTRIBUTING.md)
- [Código de Conduta](./CODE_OF_CONDUCT.md)
- [Política de Segurança](./SECURITY.md)
- [Changelog](./CHANGELOG.md)
- [Licença](./LICENSE)
