# Arquitetura de IA do ColaboraPANC

## Objetivo da camada de IA
Fornecer **sugestão assistiva** de identificação botânica a partir de imagem, com score de confiança, top-k e trilha auditável para revisão humana.

## Componentes implementados

### 1) Orquestração de inferência
- Módulo em `mapping/services/ia_identificacao/` com:
  - `factory.py` para instanciar providers.
  - `plantnet_provider.py` e `plantid_provider.py`.
  - `schemas.py` para normalização (`ResultadoInferencia`, `PredicaoNormalizada`).
- Função exposta: `identificar_com_multiplos_provedores(...)`.

### 2) Endpoint de execução
- `POST /api/cientifico/pontos/<ponto_id>/inferencia/`
- Implementado em `InferenciaPontoAPIView`.
- Requisitos:
  - ponto existente,
  - imagem válida,
  - autenticação.

### 3) Armazenamento científico
- `PredicaoIA`: resultado estruturado da inferência.
- `ValidacaoEspecialista`: decisão humana final.
- `HistoricoValidacao`: eventos auditáveis do ciclo.

## Como a inferência funciona
1. Recebe foto do ponto.
2. Consulta providers configurados (PlantNet obrigatório, Plant.id quando chave disponível).
3. Normaliza resultados para top-k.
4. Define score global e faixa operacional (`alto`, `medio`, `baixo`).
5. Marca se revisão humana é requerida.
6. Atualiza campos sugeridos no ponto.

## Definições operacionais
- **Top-k**: lista das k hipóteses mais prováveis (no código atual, até 3).
- **Score de confiança**: valor contínuo (0–1 internamente; também persistido em % no ponto).
- **Faixa de risco/confiabilidade**:
  - alto: score ≥ 0.85
  - médio: 0.60 ≤ score < 0.85
  - baixo: score < 0.60

## Explicabilidade disponível
- Justificativa textual por predição (`justificativa`).
- Componentes do score territorial no dashboard (`componentes`).
- Histórico de eventos em `HistoricoValidacao`.

## Limitações atuais
- Dependência de APIs de terceiros e chaves válidas.
- Ausência de modelo próprio treinado localmente no backend.
- Sem calibragem estatística formal de confiança por espécie/bioma.

## Princípio de governança
A IA **não decide sozinha**. Decisões de validação final são humanas via papel de revisor/admin.
