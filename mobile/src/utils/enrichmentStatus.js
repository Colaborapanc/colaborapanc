export const ENRICHMENT_STATUS = {
  completo: { label: 'Validado', color: '#16A34A', bg: '#DCFCE7', icon: 'checkmark-circle' },
  parcial: { label: 'Parcialmente validado', color: '#D97706', bg: '#FEF3C7', icon: 'alert-circle' },
  pendente: { label: 'Pendente', color: '#64748B', bg: '#E2E8F0', icon: 'time' },
  falho: { label: 'Falha temporária', color: '#DC2626', bg: '#FEE2E2', icon: 'warning' },
};

export const getEnrichmentStatusUI = (status) => ENRICHMENT_STATUS[status] || ENRICHMENT_STATUS.pendente;

const toArray = (value) => {
  if (Array.isArray(value)) return value;
  if (typeof value === 'string' && value.trim()) {
    return value.split(',').map((item) => item.trim()).filter(Boolean);
  }
  return [];
};

const formatArrayOrFallback = (value, fallback = 'Não informado') => {
  const array = toArray(value).filter((item) => item && item !== 'nao_informado');
  return array.length ? array.join(', ') : fallback;
};

const formatComestibilidade = (raw) => {
  if (raw === 'sim') return 'Sim';
  if (raw === 'nao') return 'Não';
  return 'Não informado';
};

export const normalizeEnrichmentData = (ponto = {}) => {
  const parteComestivel = formatArrayOrFallback(ponto.parte_comestivel_lista || ponto.parte_comestivel);
  const frutificacao = formatArrayOrFallback(ponto.frutificacao_meses || ponto.epoca_frutificacao);
  const colheitaRaw = ponto.colheita_periodo;
  const colheita = Array.isArray(colheitaRaw)
    ? formatArrayOrFallback(colheitaRaw)
    : (colheitaRaw && colheitaRaw !== 'nao_informado' ? colheitaRaw : (ponto.epoca_colheita || 'Não informado'));

  return {
    nome_cientifico_submetido: ponto.nome_cientifico_submetido || ponto.nome_cientifico || '',
    nome_cientifico_validado: ponto.nome_cientifico_validado || '',
    nome_aceito: ponto.nome_aceito || '',
    autoria: ponto.autoria || '',
    sinonimos: Array.isArray(ponto.sinonimos) ? ponto.sinonimos : [],
    fonte_taxonomica_primaria: ponto.fonte_taxonomica_primaria || '',
    fontes_taxonomicas_secundarias: Array.isArray(ponto.fontes_taxonomicas_secundarias) ? ponto.fontes_taxonomicas_secundarias : [],
    grau_confianca_taxonomica: Number(ponto.grau_confianca_taxonomica ?? ponto.grau_confianca ?? 0),
    distribuicao_resumida: ponto.distribuicao_resumida || '',
    ocorrencias_gbif: Number(ponto.ocorrencias_gbif || 0),
    ocorrencias_inaturalist: Number(ponto.ocorrencias_inaturalist || 0),
    fenologia_observada: ponto.fenologia_observada || '',
    imagem_url: ponto.imagem_url || '',
    imagem_fonte: ponto.imagem_fonte || '',
    licenca_imagem: ponto.licenca_imagem || '',
    ultima_validacao_em: ponto.ultima_validacao_em || null,
    status_enriquecimento: ponto.status_enriquecimento || ponto.selo_enriquecimento || 'pendente',
    validacao_pendente_revisao_humana: Boolean(ponto.validacao_pendente_revisao_humana),
    comestibilidade_status: ponto.comestibilidade_status || 'indeterminado',
    comestibilidade_confirmada: Boolean(ponto.comestibilidade_confirmada),
    comestibilidade_label: formatComestibilidade(ponto.comestibilidade_status),
    parte_comestivel: parteComestivel,
    parte_comestivel_confirmada: Boolean(ponto.parte_comestivel_confirmada),
    frutificacao_meses: frutificacao,
    frutificacao_confirmada: Boolean(ponto.frutificacao_confirmada),
    colheita_periodo: colheita,
    colheita_confirmada: Boolean(ponto.colheita_confirmada),
    integracoes_utilizadas: Array.isArray(ponto.integracoes_utilizadas) ? ponto.integracoes_utilizadas : [],
    integracoes_com_falha: Array.isArray(ponto.integracoes_com_falha) ? ponto.integracoes_com_falha : [],
  };
};

export const getFallbackEnrichmentText = (status) => {
  if (status === 'parcial') return 'Enriquecimento parcial: algumas integrações não responderam.';
  if (status === 'falho') return 'Falha temporária de integração. Tente revalidar em instantes.';
  return '';
};
