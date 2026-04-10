# ColaboraPANC

Plataforma colaborativa para registro georreferenciado de PANCs, com fluxo de identificação assistida por IA, revisão humana e análise territorial.

## Problema que o projeto resolve
O projeto busca organizar observações de PANCs em campo com rastreabilidade: quem cadastrou, onde, qual inferência automatizada foi gerada, qual revisão humana foi aplicada e qual o estado final da validação.

## Núcleo científico e tecnológico
- **Geodados** com `PointField` (GeoDjango/PostGIS) no modelo `PontoPANC`.
- **Inferência assistiva** com provedores externos (PlantNet e Plant.id) normalizados em estrutura comum.
- **Humano-no-loop** com modelos `PredicaoIA`, `ValidacaoEspecialista` e `HistoricoValidacao`.
- **Priorização territorial** por heurística explícita e reprodutível.
- **Métricas analíticas** via endpoint de dashboard científico.

## Estado atual das funcionalidades

### IMPLEMENTADO
- Cadastro e visualização de pontos PANC no backend Django.
- Upload de imagem por ponto e execução de inferência IA no endpoint científico.
- Fila de revisão com restrição por papel (`Revisor` ou superusuário).
- Validação humana de pontos com trilha de histórico.
- Busca avançada de pontos por filtros textuais, status e bounding box.
- APIs para notificações, mensagens, rotas e preferências de usuário.
- Integração de alertas ambientais (INMET/Open-Meteo/MapBiomas) com endpoints dedicados.
- App mobile Expo/React Native com telas principais de mapa, cadastro, perfil e revisão.

### PARCIALMENTE IMPLEMENTADO
- Push notifications: registro de token e modelo persistente existem, envio efetivo depende de configuração operacional.
- Offline mobile: APIs e modelos de pacotes/plantas offline existem; uso em produção depende de estratégia de sincronização e volume de dados.
- AR e identificação avançada: modelos, endpoints e telas estão presentes, mas a maturidade varia conforme ativos 3D e infraestrutura.
- Recomendação de PANC/e-commerce: modelos e endpoints estão no código, porém o pipeline de atualização/sincronização é limitado.

### PLANEJADO / FUTURO
- Evolução de métricas científicas avançadas (ex.: precisão/recall/F1 com base validada robusta).
- Endurecimento operacional de governança de dados e anonimização geográfica por contexto.
- Consolidação arquitetural (redução de duplicidades entre fluxos legados e novos).

## Arquitetura resumida
- **Backend**: Django 4.2 + Django REST Framework (`mapping` como app central).
- **Banco**: PostgreSQL + PostGIS.
- **Frontend mobile**: Expo + React Native.
- **Integrações externas**: PlantNet, Plant.id, Open-Meteo, INMET, MapBiomas.

## Stack real
- Python, Django, DRF, GeoDjango
- PostgreSQL/PostGIS
- JavaScript, React Native, Expo
- Bibliotecas geoespaciais (GDAL) e processamento de imagem (Pillow)

## Estrutura do repositório (resumo)
- `config/`: configuração do Django (settings/urls/wsgi/asgi).
- `mapping/`: modelos, views, serializers, serviços e rotas principais.
- `mobile/`: app mobile Expo com telas, serviços e navegação.
- `tests/`: testes automatizados de serviços e permissões.
- `docs/`: documentação técnica auditável.

## Requisitos
- Python 3.11+
- PostgreSQL com extensão PostGIS
- GDAL no sistema
- Node.js + npm para mobile

## Instalação rápida
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements_core.txt
cp .env.example .env  # se existir
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

Mobile:
```bash
cd mobile
npm install
npm start
```

## Testes
```bash
pytest
```

## Documentação detalhada
- [Arquitetura geral](docs/arquitetura_geral.md)
- [Arquitetura de IA](docs/arquitetura_ia_colaborapanc.md)
- [Fluxo científico](docs/fluxo_cientifico_do_sistema.md)
- [Instalação backend](docs/instalacao_backend.md)
- [Instalação mobile](docs/instalacao_mobile.md)
- [Configuração de ambiente](docs/configuracao_ambiente.md)
- [Modelos de dados](docs/modelos_de_dados.md)
- [API endpoints](docs/api_endpoints.md)
- [Priorização territorial](docs/priorizacao_territorial.md)
- [Métricas e validação](docs/metricas_e_validacao.md)
- [Governança de IA](docs/governanca_ia.md)
- [Política de dados e privacidade](docs/politica_dados_e_privacidade.md)
- [Testes](docs/testes.md)
- [Deploy](docs/deploy.md)
- [Troubleshooting](docs/troubleshooting.md)
- [Roadmap](docs/roadmap.md)
- [AR e Identificação Avançada](docs/feature_ar_identificacao.md)
- [Padrão de documentação bilíngue / Bilingual documentation standard](docs/documentacao_bilingue_padrao.md)

## Status do projeto
Projeto funcional com núcleo científico implementado no backend; ainda há áreas com implementação parcial e heterogeneidade entre módulos legados e módulos novos.

## Licença
Este projeto está licenciado sob a [MIT License](LICENSE).

## Citação
Se você usar o ColaboraPANC em sua pesquisa, por favor cite usando o arquivo [CITATION.cff](CITATION.cff) ou o formato abaixo:

```
ColaboraPANC Contributors (2026). ColaboraPANC: AI-Assisted Geo-Referenced Mapping and
Human-in-the-Loop Validation of Non-Conventional Food Plants. MIT License.
https://github.com/warleynutricionista-jpg/colaborapanc
```

## Contribuição
Consulte [CONTRIBUTING.md](CONTRIBUTING.md) para orientações sobre como contribuir.

## Segurança
Leia [SECURITY.md](SECURITY.md) antes de reportar vulnerabilidades.

## Contato
Equipe ColaboraPANC (manutenção técnica do repositório).

## Nota sobre uso de IA
A IA no ColaboraPANC é **assistiva**: gera hipóteses com score de confiança e não substitui decisão humana especializada.
