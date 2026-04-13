# Fluxo científico do sistema

## Fluxo principal
`cadastro -> imagem -> inferência -> revisão -> validação -> métricas -> priorização territorial`

## 1. Cadastro do ponto
- Entidade: `PontoPANC`.
- Dados principais: planta, localização geográfica, contexto textual e foto.
- Estado inicial típico: `status_fluxo='rascunho'` e `status_validacao='pendente'`.
- Campos alimentares/sazonais expostos no cadastro e edição:
  - `comestibilidade_status` (`sim`/`nao`/`indeterminado`)
  - `parte_comestivel_manual`
  - `frutificacao_manual`
  - `colheita_manual`
- Precedência de preenchimento:
  1. dado local validado cientificamente;
  2. dado local já confirmado por fluxo interno;
  3. dado manual do usuário;
  4. enriquecimento automático por integrações;
  5. não informado.

## 2. Submissão de imagem
- O ponto precisa de `foto` para disparar inferência científica.
- Validações de arquivo são aplicadas no endpoint de inferência.

## 3. Inferência IA
- Endpoint: `POST /api/cientifico/pontos/<id>/inferencia/`.
- Resultado persistido em `PredicaoIA` com:
  - provedor,
  - `predicoes_top_k`,
  - `score_confianca`,
  - `faixa_risco`,
  - `requer_revisao_humana`.
- Atualiza sugestão no ponto (`nome_popular_sugerido`, `nome_cientifico_sugerido`, `score_identificacao`).

## 4. Fila de revisão
- Endpoint: `GET /api/cientifico/revisao/fila/`.
- Acesso restrito a revisor/admin.
- Filtros: faixa de confiança, status e janela de dias.

## 5. Revisão e validação humana
- Endpoint: `POST /api/cientifico/pontos/<id>/validacao/`.
- Registro em `ValidacaoEspecialista`.
- Atualização do ponto para `validado`, `rejeitado` ou `necessita_revisao`.

## 6. Divergência IA vs humano
- Campo de justificativa de divergência: `motivo_divergencia`.
- Permite registrar espécie final escolhida pelo especialista.

## 7. Histórico auditável
- Eventos ficam em `HistoricoValidacao` (`predicao_ia_gerada`, `validacao_humana`, etc.).
- Endpoint: `GET /api/cientifico/pontos/<id>/historico/`.
- Enriquecimento por ponto registra também:
  - `payload_resumido_validacao.campos_fontes`
  - `payload_resumido_validacao.divergencias_campos_locais`
  - `payload_resumido_validacao.ambiguidade_taxonomica`
  - `validacao_pendente_revisao_humana` quando houver conflito taxonômico, baixa confiança ou múltiplos nomes científicos plausíveis.

## 10. Regras de enriquecimento automático (cadastro/edição)
- Busca com prioridade:
  1. `nome_cientifico` validado/submetido;
  2. nome científico sugerido;
  3. fallback por nome popular (base local) quando necessário.
- Integrações tentadas no pipeline: Global Names, Tropicos, GBIF, iNaturalist, Trefle e Wikipedia/Wikimedia (campos-alvo curtos).
- Sem evidência suficiente, os campos alimentares permanecem como "Não informado" (sem inferir "Não" por ausência de dado).
- A UI comum não exibe o estado técnico `status_enriquecimento=pendente`; esse estado segue interno para auditoria/admin.

## 8. Métricas científicas
- Endpoint: `GET /api/cientifico/dashboard/`.
- Indicadores: taxa de validação/rejeição, concordância IA-especialista, tempo médio de validação, distribuição por confiança.

## 9. Priorização territorial
- Serviço `calcular_score_prioridade(...)` combina incidência, clima, confiabilidade e recência.
- Resultado usado no dashboard como amostra operacional.
