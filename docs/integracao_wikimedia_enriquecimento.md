# Integração Wikimedia/Wikipedia no enriquecimento controlado

## Objetivo
Adicionar a Wikimedia/Wikipedia como **fonte complementar** para preencher apenas 4 campos:
- Comestível
- Parte comestível
- Frutificação
- Colheita

Sem substituir o fluxo científico local, sem expandir para perfil enciclopédico e sem poluir a interface.

## Arquitetura
Camadas isoladas:
1. **Cliente HTTP externo**: `mapping/services/external/wikimedia_client.py`
2. **Extratores de campos-alvo**: `mapping/services/enrichment/field_extractors.py`
3. **Orquestração do enriquecimento Wikimedia**: `mapping/services/enrichment/wikipedia_enrichment_service.py`
4. **Compatibilidade com pipeline atual**: `mapping/services/enrichment/planta_enrichment_pipeline.py`

## Política de precedência de dados
1. Dado local já confirmado (`*_confirmada=True`) sempre prevalece.
2. Dado consolidado por fluxo interno continua prioridade.
3. Wikipedia/Wikimedia só preenche lacunas com evidência confirmada.
4. Ausência de evidência **não** gera “Não” para comestibilidade.

Quando há divergência com valor local confirmado, o sistema:
- mantém o valor local,
- registra a divergência em `payload_resumido_validacao.divergencias_campos_locais`.

## Estratégia de resolução de página
Ordem de tentativa:
1. Nome científico validado
2. Nome científico sugerido
3. Nome popular principal
4. Variações normalizadas simples

Idioma:
- Prioridade: `pt`
- Fallback controlado: `en`

Validação mínima:
- score de aderência semântica,
- bloqueio de páginas ambíguas/desambiguação,
- rejeição de baixa confiança (`WIKIMEDIA_MIN_MATCH_CONFIDENCE`).

## Campos enriquecidos e normalização
Saída normalizada para o pipeline:
- `comestibilidade_status`: `sim | nao | indeterminado`
- `parte_comestivel`: lista curta normalizada
- `frutificacao_meses`: lista curta (`jan`..`dez`) quando possível
- `colheita_periodo`: lista curta ou string curta

Campos sem evidência permanecem não preenchidos.

## Rastreabilidade
Para cada execução, o pipeline grava:
- status do enriquecimento Wikimedia,
- título e idioma da página,
- confiança de correspondência,
- tentativas resumidas de resolução,
- evidência por campo extraído,
- divergências com dados locais confirmados,
- erro classificado quando existir.

Tudo é salvo no JSON de auditoria (`payload_resumido_validacao`) sem quebrar schema atual.

## Cache e uso responsável
- Cache por consulta (`search`) e por página (`extract`) com TTL configurável.
- Evita chamadas repetidas para mesmos títulos/consultas.
- Requisições com timeout/retry e circuit breaker herdados do cliente HTTP resiliente.

## Identificação obrigatória do cliente
Configurações centralizadas no `settings.py` e `.env`:
- `WIKIMEDIA_USER`
- `WIKIMEDIA_EMAIL`
- `WIKIMEDIA_USER_AGENT`
- `WIKIMEDIA_API_USER_AGENT`

Formato recomendado:
`ColaboraPANC/<versao> (Warleyalisson; warleyalisson@gmail.com)`

## Comportamento em indisponibilidade externa
Erros são classificados (timeout, rate limit, rede, ambiguidade, conteúdo insuficiente etc.) e:
- não quebram cadastro/revalidação,
- não expõem erro bruto para usuário final,
- mantêm fallback seguro (`indeterminado`/não preenchido).

## UX pública (cadastro e detalhe)
- O status interno `"pendente"` de enriquecimento não é exibido para usuário comum.
- A tela pública mostra apenas dados úteis:
  - valores confirmados para comestibilidade/parte comestível/frutificação/colheita;
  - `Não informado` quando não houver evidência suficiente.
- O estado técnico permanece disponível apenas em bloco administrativo.

## Fluxo de cadastro com autocomplete
- O campo **Nome popular** usa debounce e combina fontes:
  1. base local validada;
  2. histórico local de pontos;
  3. fallback externo (iNaturalist autocomplete) com cache.
- Ao escolher uma sugestão com correspondência exata, o **Nome científico** é auto-preenchido.
- A origem da resolução é persistida no payload operacional (`payload_resumido_validacao.resolucao_nome`) sem poluir a interface.

## Limitações
- Extração textual depende de padrões linguísticos (pt/en), podendo não cobrir todos os formatos de página.
- Em páginas muito curtas, o sistema pode manter campos como não informados por segurança.
- Wikipedia não substitui validação científica local.
