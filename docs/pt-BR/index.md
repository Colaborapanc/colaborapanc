# Documentação ColaboraPANC (PT-BR)

> Troca de idioma: [Português (Brasil)](./index.md) | [English](../en/index.md)

Esta é a árvore canônica de documentação em português brasileiro para o estado atual do código do ColaboraPANC.

## Navegação principal

- [Instalação](./instalacao.md)
- [Implantação](./implantacao.md)
- [Arquitetura](./arquitetura.md)
- [API](./api.md)
- [Integrações](./integracoes.md)
- [Módulos](./modulos.md)
- [Administração](./admin.md)
- [Administração: Anexo Governança Algorítmica](./governanca-algoritmica-admin.md)
- [Administração: Anexo Política de Dados e Privacidade](./politica-dados-privacidade-admin.md)
- [Guia do Usuário](./guia-do-usuario.md)
- [Contribuição](./contribuicao.md)
- [Roadmap](./roadmap.md)
- [FAQ](./faq.md)
- [Fluxos Mobile e Recursos Avançados (Anexo Técnico)](./fluxos-mobile-avancados.md)
- [Citação e release do software](./citacao.md)

## O que estes documentos representam

Este conjunto canônico reflete comportamento ativo do sistema implementado no repositório, incluindo:

- Composição de rotas web/API em Django + DRF.
- Endpoints do fluxo científico para inferência de IA, fila de revisão, validação e histórico de decisões.
- Capacidades ambientais/territoriais (MapBiomas e pipeline de alertas climáticos).
- APIs de paridade mobile e integração com cliente Expo/React Native.
- Módulos auxiliares de colaboração (notificações, conversas, gamificação, rotas, preferências).
- Base atual de testes e operação.

## Referências de código usadas para manter este índice aderente

- Registro de URLs e endpoints: `mapping/urls.py`, `config/urls.py`.
- Serviços e módulos de domínio: `mapping/services/`, `mapping/domains/`, `mapping/views*.py`, `mapping/models.py`.
- Scripts/dependências do app mobile: `mobile/package.json`, `mobile/src/*`.
- Suíte de testes: `tests/*.py`.

## Pontos de entrada relacionados

- Hub de documentação: [`docs/README.md`](../README.md)
- README raiz do projeto (PT-BR): [`README.pt-BR.md`](../../README.pt-BR.md)
- README raiz do projeto (EN): [`README.md`](../../README.md)
- Índice legado em português: [`docs/pt/README.md`](../pt/README.md)
- Índice legado em inglês: [`docs/en/README.md`](../en/README.md)
- Matriz de consolidação de legado: [`matriz-consolidacao-legado.md`](./matriz-consolidacao-legado.md)
